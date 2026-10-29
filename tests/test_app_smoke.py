import unittest
from pathlib import Path

from streamlit.testing.v1 import AppTest


ROOT = Path(__file__).resolve().parents[1]


class AppSmokeTests(unittest.TestCase):
    def test_wizard_reaches_results(self):
        app = AppTest.from_file(str(ROOT / "main.py"), default_timeout=45).run()
        self.assertFalse(app.exception)
        self.assertTrue(any("Passo 1" in heading.value for heading in app.header))

        app.button[0].click().run()
        self.assertFalse(app.exception)
        self.assertTrue(any("Passo 2" in heading.value for heading in app.header))

        app.button[1].click().run()
        self.assertFalse(app.exception)
        self.assertTrue(any("Passo 3" in heading.value for heading in app.header))

        app.button[1].click().run()
        self.assertFalse(app.exception)
        self.assertTrue(any("Resultado" in heading.value for heading in app.header))
        self.assertGreaterEqual(len(app.metric), 5)


if __name__ == "__main__":
    unittest.main()
