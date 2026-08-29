package com.fabric.adp.application;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;

import com.fabric.adp.domain.Corpus;
import com.fabric.adp.domain.NotFoundException;
import org.junit.jupiter.api.Test;

class CorpusServiceTest {

  private final CorpusService corpora = new CorpusService(new InMemoryCorpusStore().seedDemo());

  @Test
  void publishedLookupReturnsSearchEndpointNotRouteUrl() {
    Corpus row = corpora.get("policy-engine");
    assertThat(row.displayName()).isEqualTo("Policy engine");
    assertThat(row.url()).isEqualTo(CorpusGatewayUrls.ASSISTANT);
    assertThat(row.collection()).isEqualTo("policy-engine");
    assertThat(row.auth()).isEqualTo("workload-oauth");
    assertThat(row.owner()).isEqualTo("policy-ops");
    assertThat(row.status()).isEqualTo("published");
    assertThat(row.region()).isNull();
  }

  @Test
  void twoScopeIdsAreTwoCatalogRowsSharingTheGatewayUrl() {
    Corpus clauses = corpora.get("clause-index");
    Corpus playbook = corpora.get("legal-playbook");
    assertThat(clauses.url()).isEqualTo(playbook.url());
    assertThat(clauses.collection()).isEqualTo("clause-index");
    assertThat(playbook.collection()).isEqualTo("legal-playbook");
    assertThat(clauses.corpusId()).isNotEqualTo(playbook.corpusId());
  }

  @Test
  void policyAndLegalCorporaUseDifferentGatewayHosts() {
    assertThat(corpora.get("policy-engine").url()).isEqualTo(CorpusGatewayUrls.ASSISTANT);
    assertThat(corpora.get("clause-index").url()).isEqualTo(CorpusGatewayUrls.LEGAL);
    assertThat(corpora.get("research-index").url())
        .isEqualTo(CorpusGatewayUrls.dedicated("research-index"));
  }

  @Test
  void listPublishedOmitsDrafts() {
    assertThat(corpora.listPublished())
        .extracting(Corpus::corpusId)
        .contains("policy-engine", "clause-index", "legal-playbook")
        .doesNotContain("research-index");
    assertThat(corpora.listAll()).extracting(Corpus::corpusId).contains("research-index");
  }

  @Test
  void draftIsStillGettableById() {
    Corpus row = corpora.get("research-index");
    assertThat(row.status()).isEqualTo("draft");
  }

  @Test
  void missingCorpusIsNotFound() {
    assertThatThrownBy(() -> corpora.get("missing-index"))
        .isInstanceOf(NotFoundException.class)
        .hasMessageContaining("missing-index");
  }
}
