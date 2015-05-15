import unittest2 as unittest
import numpy as np

from vsm.corpus import Corpus
from vsm.corpus.util.corpusbuilders import random_corpus
from vsm.model.ldacgsmulti import *
from multiprocessing import Process

class MPTester:
    def test_demo_LdaCgsMulti(self):
        from vsm.model.ldacgsmulti import demo_LdaCgsMulti
        demo_LdaCgsMulti()
    
    def test_LdaCgsMulti_IO(self):
        from tempfile import NamedTemporaryFile
        import os
    
        c = random_corpus(1000, 50, 6, 100)
        tmp = NamedTemporaryFile(delete=False, suffix='.npz')
        try:
            m0 = LdaCgsMulti(c, 'document', K=10)
            m0.train(n_iterations=20)
            m0.save(tmp.name)
            m1 = LdaCgsMulti.load(tmp.name)
            assert m0.context_type == m1.context_type
            assert m0.K == m1.K
            assert (m0.alpha == m1.alpha).all()
            assert (m0.beta == m1.beta).all()
            assert m0.log_probs == m1.log_probs
            for i in xrange(max(len(m0.corpus), len(m1.corpus))):
                assert m0.corpus[i].all() == m1.corpus[i].all()
            assert m0.V == m1.V
            assert m0.iteration == m1.iteration
            for i in xrange(max(len(m0.Z), len(m1.Z))):
                assert m0.Z[i].all() == m1.Z[i].all()
            assert m0.top_doc.all() == m1.top_doc.all()
            assert m0.word_top.all() == m1.word_top.all()
            assert m0.inv_top_sums.all() == m1.inv_top_sums.all()
            m0 = LdaCgsMulti(c, 'document', K=10)
            m0.train(n_iterations=20)
            m0.save(tmp.name)
            m1 = LdaCgsMulti.load(tmp.name)
            assert not hasattr(m1, 'log_prob')
        finally:
            os.remove(tmp.name)

class TestLdaCgsMulti(unittest.TestCase):
    def setUp(self):
        pass
    
    def test_demo_LdaCgsMulti(self):
        t = MPTester()
        p = Process(target=t.test_demo_LdaCgsMulti, args=())
        p.start()
        p.join()
    
    def test_demo_LdaCgsMulti_IO(self):
        t = MPTester()
        p = Process(target=t.test_LdaCgsMulti_IO, args=())
        p.start()
        p.join()

if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestLdaCgsMulti)
    unittest.TextTestRunner(verbosity=2).run(suite)