package com.fabric.registry.application;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;

import com.fabric.registry.domain.CapabilityVersion;
import com.fabric.registry.domain.NotFoundException;
import com.fabric.registry.domain.PublishedConflictException;
import com.fasterxml.jackson.databind.ObjectMapper;
import java.io.InputStream;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;

class CapabilityServiceTest {

  private final ObjectMapper mapper = new ObjectMapper();
  private CapabilityService service;

  @BeforeEach
  void setUp() {
    service = new CapabilityService(new InMemoryCapabilityStore());
  }

  @Test
  void publishesFixtureAndGetsIt() throws Exception {
    CapabilityVersion published = service.put(fixture("published"));
    assertThat(published.published()).isTrue();
    assertThat(service.get("account_fee_lookup", "1.0.0", "ar").published()).isTrue();
  }

  @Test
  void secondPublishedPutConflicts() throws Exception {
    service.put(fixture("published"));
    assertThatThrownBy(() -> service.put(fixture("published")))
        .isInstanceOf(PublishedConflictException.class);
  }

  @Test
  void arCannotReadDraft() {
    service.put(
        new CapabilityVersion(
            "account_fee_lookup",
            "1.0.0",
            "domain",
            "draft",
            "{}",
            "{}",
            "{}",
            null,
            "accounts",
            "draft"));
    assertThatThrownBy(() -> service.get("account_fee_lookup", "1.0.0", "ar"))
        .isInstanceOf(NotFoundException.class);
    assertThat(service.get("account_fee_lookup", "1.0.0", "acr").draft()).isTrue();
  }

  @Test
  void searchPublishedReturnsLatestPerId() {
    service.put(cap("ocr_extract", "1.0.0", "published", "old extract"));
    service.put(cap("ocr_extract", "1.2.0", "published", "Extract text from a document id."));
    service.put(cap("ocr_extract", "1.3.0", "draft", "next extract"));
    service.put(cap("search_transactions", "1.4.0", "published", "Search transactions"));
    assertThat(service.searchPublished(""))
        .extracting(CapabilityVersion::id)
        .containsExactly("ocr_extract", "search_transactions");
    assertThat(service.latestPublished("ocr_extract").version()).isEqualTo("1.2.0");
    assertThat(service.searchPublished("document"))
        .extracting(CapabilityVersion::id)
        .containsExactly("ocr_extract");
  }

  @Test
  void listAllIncludesDraftAndRetired() {
    service.put(cap("ocr_extract", "1.1.0", "published", "old extract"));
    service.put(cap("ocr_extract", "1.2.0", "published", "Extract text from a document id."));
    service.put(cap("invoice_intake", "0.1.0", "draft", "draft intake"));
    service.put(cap("fax_ocr_legacy", "0.9.0", "retired", "retired fax"));
    assertThat(service.listAll(""))
        .extracting(CapabilityVersion::id)
        .contains("ocr_extract", "invoice_intake", "fax_ocr_legacy");
    assertThat(service.searchPublished(""))
        .extracting(CapabilityVersion::id)
        .contains("ocr_extract")
        .doesNotContain("invoice_intake", "fax_ocr_legacy");
    assertThat(service.get("fax_ocr_legacy", "0.9.0", "ar").status()).isEqualTo("retired");
    assertThat(service.latest("invoice_intake", "acp").status()).isEqualTo("draft");
  }

  @Test
  void versionsNewestFirstAndArSkipsDrafts() {
    service.put(cap("ocr_extract", "1.0.0", "published", "old"));
    service.put(cap("ocr_extract", "1.2.0", "draft", "next"));
    assertThat(service.versions("ocr_extract", "acp"))
        .extracting(CapabilityVersion::version)
        .containsExactly("1.2.0", "1.0.0");
    assertThat(service.versions("ocr_extract", "ar"))
        .extracting(CapabilityVersion::version)
        .containsExactly("1.0.0");
  }

  private static CapabilityVersion cap(String id, String version, String status, String description) {
    return new CapabilityVersion(
        id, version, "domain", description, "{}", "{}", "{}", null, "document-intel", status);
  }

  private CapabilityVersion fixture(String status) throws Exception {
    try (InputStream in =
        getClass().getResourceAsStream("/contracts/capability-account-fee-lookup.json")) {
      var tree = mapper.readTree(in);
      return new CapabilityVersion(
          tree.get("id").asText(),
          tree.get("version").asText(),
          tree.get("kind").asText(),
          tree.get("description").asText(),
          mapper.writeValueAsString(tree.get("input_schema")),
          mapper.writeValueAsString(tree.get("output_schema")),
          mapper.writeValueAsString(tree.get("invoke")),
          null,
          tree.get("owner").asText(),
          status);
    }
  }
}
