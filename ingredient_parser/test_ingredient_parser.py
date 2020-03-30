import pytest
import ingredient_parser


parser = ingredient_parser.IngredientParser()

class TestClass:

    def test_001(self):
        assert parser.parse(r"1/2 cup half-and-half") == "half and half"

    def test_002(self):
        assert parser.parse(r"1 1/4 cups all-purpose flour") == "flour"

    def test_003(self):
        assert parser.parse(r"2 eggs") == "egg"

    def test_004(self):
        assert parser.parse(r"1/2 tablespoon butter, melted") == "butter"

    def test_005(self):
        assert parser.parse(r"1/2 cup frozen blueberries, thawed") == "blueberry"

    def test_006(self):
        assert parser.parse(r"1/4 lemon, juiced (optional)") == "lemon"

    def test_007(self):
        assert parser.parse(r"1 tablespoon confectioners' sugar, or to taste (optional)") == "confectioners sugar"

    def test_008(self):
        assert parser.parse(r"1/2 (16 ounce) package linguine pasta") == "pasta"

    def test_009(self):
        assert parser.parse(r"2 tablespoons chopped fresh parsley, or to taste") == "parsley"

    def test_010(self):
        assert parser.parse(r"24 large shrimp in shell (21 to 25 per lb), peeled and deveined") == "shrimp"

    def test_011(self):
        assert parser.parse(r"1 pound large shrimp, peeled and deveined") == "shrimp"

    def test_012(self):
        assert parser.parse(r"1 1/2 teaspoons ground cinnamon") == "cinnamon"

    def test_013(self):
        assert parser.parse(r"1 dash hot pepper sauce (such as Frank's RedHot®), or to taste") == "hot sauce"

    def test_014(self):
        assert parser.parse(r"2 russet potatoes, scrubbed and cut into eighths") == "potato"

    def test_015(self):
        assert parser.parse(r"ground black pepper to taste") == None

    def test_016(self):
        assert parser.parse(r"skewers") == None

    def test_017(self):
        assert parser.parse(r"assorted colors coloring") == None

    def test_018(self):
        assert parser.parse(r"Fresh raspberries") == "raspberry"

    def test_019(self):
        assert parser.parse(r"2 pounds skinless, boneless chicken breast halves") == "chicken breast"
