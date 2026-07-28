"""Unit and integration tests for the Agent Memory & Knowledge System."""

import time
import unittest

from tools.browser.memory.models import MemoryItem, MemoryType
from tools.browser.memory.vector_store import LightweightTFIDFStore
from tools.browser.memory.scorer import MemoryScorer
from tools.browser.memory.manager import MemoryManager
from tools.browser.memory.working import WorkingMemory
from tools.browser.memory.episodic import EpisodicMemory
from tools.browser.memory.semantic import SemanticMemory
from tools.browser.memory.procedural import ProceduralMemory


class TestVectorStore(unittest.TestCase):
    def setUp(self):
        self.store = LightweightTFIDFStore()

    def test_add_and_search(self):
        item1 = MemoryItem(content="github login requires 2fa", memory_type=MemoryType.SEMANTIC)
        item2 = MemoryItem(content="how to bake a cake", memory_type=MemoryType.SEMANTIC)
        
        self.store.add(item1)
        self.store.add(item2)
        
        results = self.store.search("github 2fa login")
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0][0].id, item1.id)

    def test_remove_and_clear(self):
        item1 = MemoryItem(content="test item", memory_type=MemoryType.SEMANTIC)
        self.store.add(item1)
        
        self.assertTrue(self.store.remove(item1.id))
        self.assertEqual(self.store.total_docs, 0)
        
        self.store.add(item1)
        self.store.clear()
        self.assertEqual(self.store.total_docs, 0)


class TestMemoryScorer(unittest.TestCase):
    def setUp(self):
        self.scorer = MemoryScorer(decay_rate=0.5, similarity_weight=0.5, recency_weight=0.3, importance_weight=0.2)

    def test_scoring_weights(self):
        item = MemoryItem(content="test", memory_type=MemoryType.EPISODIC, importance=1.0)
        # Force timestamp to 1 hour ago
        item.timestamp = time.time() - 3600
        
        score = self.scorer.score(item, semantic_similarity=1.0)
        
        self.assertAlmostEqual(score.semantic_similarity, 1.0)
        self.assertAlmostEqual(score.importance_weight, 1.0)
        # 0.5^1 = 0.5 for recency
        self.assertAlmostEqual(score.recency_weight, 0.5)
        
        # 1.0*0.5 + 0.5*0.3 + 1.0*0.2 = 0.5 + 0.15 + 0.2 = 0.85
        self.assertAlmostEqual(score.final_score, 0.85)

    def test_ranking(self):
        recent_item = MemoryItem(content="recent", memory_type=MemoryType.SEMANTIC, importance=0.5)
        recent_item.timestamp = time.time()
        
        old_item = MemoryItem(content="old", memory_type=MemoryType.SEMANTIC, importance=0.5)
        old_item.timestamp = time.time() - (3600 * 10) # 10 hours old
        
        items = [
            (old_item, 1.0),     # Perfect semantic match but very old
            (recent_item, 0.9),  # Good semantic match and very recent
        ]
        
        ranked = self.scorer.rank(items)
        
        # Recent item should win despite slightly lower semantic match due to recency decay of old item
        self.assertEqual(ranked[0][0].content, "recent")


class TestMemoryLayers(unittest.TestCase):
    def setUp(self):
        self.store = LightweightTFIDFStore()
        self.scorer = MemoryScorer()

    def test_working_memory(self):
        working = WorkingMemory()
        working.set_goal("book flight")
        working.log_step({"action": "click", "selector": "#btn"}, True, "")
        working.log_step({"action": "fill", "selector": "#input"}, False, "error")
        
        summary = working.summarize()
        self.assertEqual(summary.memory_type, MemoryType.WORKING)
        self.assertIn("book flight", summary.content)
        self.assertIn("2 (1 successful)", summary.content)
        
        working.clear()
        self.assertEqual(working.active_goal, "")
        self.assertEqual(len(working.recent_steps), 0)

    def test_episodic_memory(self):
        episodic = EpisodicMemory(self.store, self.scorer)
        episodic.log_execution("click", "#submit", True)
        episodic.log_execution("click", "#missing", False, "not found")
        
        results = episodic.retrieve_similar_experiences("missing not found")
        self.assertTrue(len(results) > 0)
        self.assertIn("missing", results[0][0].content)

    def test_semantic_memory(self):
        semantic = SemanticMemory(self.store, self.scorer)
        semantic.store_fact("github.com", "Requires 2FA for login")
        
        results = semantic.retrieve_domain_knowledge("github.com")
        self.assertEqual(len(results), 1)
        self.assertIn("2FA", results[0][0].content)

    def test_procedural_memory(self):
        procedural = ProceduralMemory(self.store, self.scorer)
        procedural.store_alternative_selector("amazon.com", "#buy-now", "#buy-box button")
        
        alternatives = procedural.get_known_selectors("amazon.com", "#buy-now")
        self.assertEqual(alternatives, ["#buy-box button"])


class TestMemoryIntegration(unittest.TestCase):
    def test_memory_manager_consolidation(self):
        manager = MemoryManager()
        
        # Simulate working session
        manager.working.set_goal("Test consolidation")
        manager.working.log_step({"action": "test"}, True, "success")
        
        # Consolidate
        manager.consolidate()
        
        # Working memory should be clear
        self.assertEqual(manager.working.active_goal, "")
        
        # Episodic should have the summary
        results = manager.episodic.retrieve_similar_experiences("Test consolidation")
        self.assertTrue(len(results) > 0)
        self.assertIn("Test consolidation", results[0][0].content)

    def test_get_relevant_context(self):
        manager = MemoryManager()
        manager.semantic.store_fact("test.com", "Site uses react")
        manager.procedural.store_strategy("login", "Enter user, enter pass, click submit")
        manager.episodic.log_execution("login", "#form", True)
        
        context = manager.get_relevant_context("how to login", domain="test.com")
        
        self.assertIn("Site uses react", context)
        self.assertIn("Enter user", context)
        self.assertIn("login", context)


if __name__ == "__main__":
    unittest.main()
