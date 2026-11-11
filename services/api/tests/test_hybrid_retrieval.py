import unittest

from services.api.services.tafsir_retrieval import (
    LEXICAL_SQL,
    SEARCH_SQL,
    reciprocal_rank_fusion,
)


class ReciprocalRankFusionTests(unittest.TestCase):
    def test_items_ranked_high_in_both_lists_win(self):
        vector = [{"passage_id": "a"}, {"passage_id": "b"}, {"passage_id": "c"}]
        lexical = [{"passage_id": "c"}, {"passage_id": "b"}, {"passage_id": "d"}]
        fused = reciprocal_rank_fusion([vector, lexical], top_k=4)
        self.assertEqual(fused[0]["passage_id"], "c")
        self.assertEqual({r["passage_id"] for r in fused}, {"a", "b", "c", "d"})

    def test_top_k_limits_and_duplicates_are_merged(self):
        lists = [[{"passage_id": "a"}, {"passage_id": "b"}], [{"passage_id": "a"}]]
        fused = reciprocal_rank_fusion(lists, top_k=1)
        self.assertEqual([r["passage_id"] for r in fused], ["a"])

    def test_empty_input(self):
        self.assertEqual(reciprocal_rank_fusion([[], []], top_k=5), [])


class LexicalSqlTests(unittest.TestCase):
    def test_lexical_sql_keeps_rights_filters_and_uses_fts(self):
        sql = str(LEXICAL_SQL)
        self.assertIn("plainto_tsquery('arabic', :query_text)", sql)
        self.assertIn("sp.verification_status::text = 'verified'", sql)
        self.assertNotIn("ORDER BY p.embedding", sql)
        self.assertIn("ORDER BY p.embedding", str(SEARCH_SQL))


if __name__ == "__main__":
    unittest.main()
