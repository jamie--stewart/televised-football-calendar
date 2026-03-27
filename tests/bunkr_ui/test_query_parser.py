from src.bunkr_ui.services.query_parser import ParsedQuery, filter_results, parse_query


class TestParseQuery:
    def test_empty_query(self):
        result = parse_query("")
        assert result.is_empty

    def test_bare_words(self):
        result = parse_query("hello world")
        assert result.optional_terms == ["hello", "world"]
        assert result.must_include == []
        assert result.must_exclude == []
        assert result.exact_phrases == []

    def test_must_include(self):
        result = parse_query("+beach +summer")
        assert result.must_include == ["beach", "summer"]
        assert result.optional_terms == []

    def test_must_exclude(self):
        result = parse_query("-amateur -low")
        assert result.must_exclude == ["amateur", "low"]

    def test_exact_phrase(self):
        result = parse_query('"hot tub"')
        assert result.exact_phrases == ["hot tub"]

    def test_mixed_query(self):
        result = parse_query('+beach -amateur "hot tub" vacation')
        assert result.must_include == ["beach"]
        assert result.must_exclude == ["amateur"]
        assert result.exact_phrases == ["hot tub"]
        assert result.optional_terms == ["vacation"]

    def test_upstream_query_must_include_first(self):
        result = parse_query("+beach vacation")
        assert result.to_upstream_query() == "beach"

    def test_upstream_query_falls_back_to_optional(self):
        result = parse_query("vacation fun")
        assert result.to_upstream_query() == "vacation fun"

    def test_upstream_query_combines_must_and_phrases(self):
        result = parse_query('+beach "hot tub"')
        assert result.to_upstream_query() == "beach hot tub"

    def test_empty_quoted_string(self):
        result = parse_query('""')
        assert result.exact_phrases == [""]

    def test_multiple_phrases(self):
        result = parse_query('"phrase one" "phrase two"')
        assert result.exact_phrases == ["phrase one", "phrase two"]


class TestFilterResults:
    def _make_results(self, titles):
        return [{"title": t} for t in titles]

    def test_must_include_filters(self):
        results = self._make_results(["Beach Party", "Mountain Trip", "Beach Vacation"])
        query = ParsedQuery(must_include=["beach"])
        filtered = filter_results(results, query)
        assert len(filtered) == 2
        assert filtered[0]["title"] == "Beach Party"
        assert filtered[1]["title"] == "Beach Vacation"

    def test_must_exclude_filters(self):
        results = self._make_results(["Beach Party", "Amateur Beach", "Beach Vacation"])
        query = ParsedQuery(must_exclude=["amateur"])
        filtered = filter_results(results, query)
        assert len(filtered) == 2
        assert all("Amateur" not in r["title"] for r in filtered)

    def test_exact_phrase_filters(self):
        results = self._make_results(["Hot Tub Party", "Hot Dog Stand", "The Hot Tub"])
        query = ParsedQuery(exact_phrases=["hot tub"])
        filtered = filter_results(results, query)
        assert len(filtered) == 2

    def test_optional_terms_ranking(self):
        results = self._make_results(["Beach", "Beach Vacation", "Beach Vacation Fun"])
        query = ParsedQuery(optional_terms=["vacation", "fun"])
        filtered = filter_results(results, query)
        assert filtered[0]["title"] == "Beach Vacation Fun"
        assert filtered[1]["title"] == "Beach Vacation"
        assert filtered[2]["title"] == "Beach"

    def test_combined_filters(self):
        results = self._make_results(["Beach Party", "Amateur Beach", "Beach Vacation", "Mountain Trip"])
        query = ParsedQuery(must_include=["beach"], must_exclude=["amateur"])
        filtered = filter_results(results, query)
        assert len(filtered) == 2
        assert all("Beach" in r["title"] for r in filtered)
        assert all("Amateur" not in r["title"] for r in filtered)

    def test_case_insensitive(self):
        results = self._make_results(["BEACH PARTY"])
        query = ParsedQuery(must_include=["beach"])
        filtered = filter_results(results, query)
        assert len(filtered) == 1
