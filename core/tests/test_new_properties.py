"""Tests for new ontology properties (OntoCore refactoring)."""

import pytest
from rdflib import Graph, Namespace, RDF, Literal, XSD

OC = Namespace("https://ontoskills.sh/ontology#")
CORE_TTL_PATH = "site/public/ontology/core.ttl"


@pytest.fixture
def core_graph():
    g = Graph()
    g.parse(CORE_TTL_PATH, format="turtle")
    return g


class TestNewDatatypeProperties:
    """Verify all 9 new DatatypeProperties exist in core.ttl."""

    EXPECTED_PROPERTIES = {
        "hasCategory": XSD.string,
        "hasVersion": XSD.string,
        "hasLicense": XSD.string,
        "hasVendor": XSD.string,
        "hasPackageName": XSD.string,
        "isUserInvocable": XSD.boolean,
        "hasArgumentHint": XSD.string,
        "hasAllowedTool": XSD.string,
        "hasAlias": XSD.string,
    }

    @pytest.mark.parametrize("prop_name,xsd_type", list(EXPECTED_PROPERTIES.items()))
    def test_property_exists_in_ontology(self, core_graph, prop_name, xsd_type):
        """Each new property must be declared as owl:DatatypeProperty."""
        prop_uri = OC[prop_name]
        OWL = Namespace("http://www.w3.org/2002/07/owl#")
        assert (prop_uri, RDF.type, OWL.DatatypeProperty) in core_graph, (
            f"oc:{prop_name} not found as owl:DatatypeProperty in core.ttl"
        )

    def test_all_9_properties_present(self, core_graph):
        """Exactly 9 new properties should be added."""
        OWL = Namespace("http://www.w3.org/2002/07/owl#")
        new_prop_names = list(self.EXPECTED_PROPERTIES.keys())
        found = 0
        for name in new_prop_names:
            if (OC[name], RDF.type, OWL.DatatypeProperty) in core_graph:
                found += 1
        assert found == 9, f"Expected 9 new properties, found {found}"

    def test_dependsOnSkill_exists_as_object_property(self, core_graph):
        """oc:dependsOnSkill MUST exist as a dedicated ObjectProperty for skill-to-skill dependencies."""
        OWL = Namespace("http://www.w3.org/2002/07/owl#")
        assert (OC.dependsOnSkill, RDF.type, OWL.ObjectProperty) in core_graph, (
            "oc:dependsOnSkill not found as owl:ObjectProperty in core.ttl"
        )

    def test_dependsOnSkill_range_is_skill(self, core_graph):
        """oc:dependsOnSkill must have rdfs:range oc:Skill."""
        RDFS = Namespace("http://www.w3.org/2000/01/rdf-schema#")
        range_val = core_graph.value(OC.dependsOnSkill, RDFS.range)
        assert str(range_val) == str(OC.Skill), (
            f"oc:dependsOnSkill range should be oc:Skill, got {range_val}"
        )


class TestNewShaclShapes:
    """Verify SHACL shapes exist for all new properties."""

    @pytest.fixture
    def shacl_graph(self):
        g = Graph()
        g.parse("core/specs/ontoskills.shacl.ttl", format="turtle")
        return g

    NEW_PROPERTIES = [
        "hasCategory", "hasVersion", "hasLicense", "hasVendor",
        "hasPackageName", "hasArgumentHint", "hasAllowedTool", "hasAlias",
    ]

    def test_skill_shape_has_optional_properties(self, shacl_graph):
        """SkillShape should have optional property shapes for all new string properties."""
        SH = Namespace("http://www.w3.org/ns/shacl#")
        skill_shape = OC.SkillShape
        found_paths = set()
        for _, _, shape_node in shacl_graph.triples((skill_shape, SH.property, None)):
            path = shacl_graph.value(shape_node, SH.path)
            if path is not None:
                local_name = str(path).split("#")[-1]
                found_paths.add(local_name)
        for prop in self.NEW_PROPERTIES:
            assert prop in found_paths, (
                f"oc:{prop} not found in SkillShape property constraints"
            )

    def test_isUserInvocable_shape_is_boolean(self, shacl_graph):
        """isUserInvocable SHACL shape should specify xsd:boolean datatype."""
        SH = Namespace("http://www.w3.org/ns/shacl#")
        skill_shape = OC.SkillShape
        for _, _, shape_node in shacl_graph.triples((skill_shape, SH.property, None)):
            path = shacl_graph.value(shape_node, SH.path)
            if path is not None and str(path).endswith("isUserInvocable"):
                datatype = shacl_graph.value(shape_node, SH.datatype)
                assert str(datatype) == str(XSD.boolean), (
                    f"isUserInvocable should have xsd:boolean datatype, got {datatype}"
                )
                return
        pytest.fail("isUserInvocable property shape not found in SkillShape")
