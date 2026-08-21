package com.fabric.adp.adapters.in.http;

import com.fabric.adp.application.CorpusService;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

@RestController
public class CorpusController {

  private final CorpusService corpora;

  public CorpusController(CorpusService corpora) {
    this.corpora = corpora;
  }

  @GetMapping("/v1/catalog/corpora")
  public Map<String, Object> list(
      @RequestParam(name = "include", required = false) String include) {
    List<Map<String, Object>> items =
        ("all".equals(include) ? corpora.listAll() : corpora.listPublished())
            .stream().map(CorpusBodies::toBody).toList();
    Map<String, Object> body = new LinkedHashMap<>();
    body.put("corpora", items);
    return body;
  }

  @GetMapping("/v1/catalog/corpora/{corpusId}")
  public Map<String, Object> get(@PathVariable String corpusId) {
    return CorpusBodies.toBody(corpora.get(corpusId));
  }
}
