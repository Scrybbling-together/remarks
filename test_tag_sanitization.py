import pytest
from remarks.utils import sanitize_obsidian_tag


class TestTagSanitization:
    """
    Comprehensive unit tests for Obsidian tag sanitization.
    
    Based on real Obsidian testing, these rules apply:
    - Tags must start with a letter (not number)
    - Alphanumeric + dash + underscore work well
    - Angle brackets completely break parsing
    - Most special characters cause issues
    - Multiple leading hashes need normalization
    """

    def test_basic_valid_tags(self):
        """Test tags that should work without modification"""
        assert sanitize_obsidian_tag("simple") == "simple"
        assert sanitize_obsidian_tag("test123") == "test123"
        assert sanitize_obsidian_tag("underscore_tag") == "underscore_tag"
        assert sanitize_obsidian_tag("tag-with-dashes") == "tag-with-dashes"
        assert sanitize_obsidian_tag("mixed_123-tag") == "mixed_123-tag"

    def test_leading_hash_removal(self):
        """Test removal of leading # characters"""
        assert sanitize_obsidian_tag("#simple") == "simple"
        assert sanitize_obsidian_tag("##double-hash") == "double-hash"
        assert sanitize_obsidian_tag("###triple") == "triple"
        assert sanitize_obsidian_tag("#tag#with#internal#hashes") == "tag-with-internal-hashes"

    def test_angle_brackets(self):
        """Test that angle brackets are replaced (they break Obsidian)"""
        assert sanitize_obsidian_tag("tag<with>angles") == "tag-with-angles"
        assert sanitize_obsidian_tag("<broken>") == "broken"
        assert sanitize_obsidian_tag("<<multiple>>") == "multiple"

    def test_spaces_replaced(self):
        """Test that spaces are replaced with dashes"""
        assert sanitize_obsidian_tag("tag with spaces") == "tag-with-spaces"
        assert sanitize_obsidian_tag("multiple word tag") == "multiple-word-tag"
        assert sanitize_obsidian_tag("a b c") == "a-b-c"

    def test_special_characters_replaced(self):
        """Test that problematic special characters are replaced with dashes"""
        assert sanitize_obsidian_tag("tag.with.dots") == "tag-with-dots"
        assert sanitize_obsidian_tag("tag,with,commas") == "tag-with-commas"
        assert sanitize_obsidian_tag("tag;with;semicolons") == "tag-with-semicolons"
        assert sanitize_obsidian_tag("tag(with)parentheses") == "tag-with-parentheses"
        assert sanitize_obsidian_tag("tag$with$dollars") == "tag-with-dollars"
        assert sanitize_obsidian_tag("tag&with&ampersands") == "tag-with-ampersands"
        assert sanitize_obsidian_tag('tag"with"quotes') == "tag-with-quotes"
        assert sanitize_obsidian_tag("tag?with?questions") == "tag-with-questions"
        assert sanitize_obsidian_tag("tag!with!exclamations") == "tag-with-exclamations"
        assert sanitize_obsidian_tag("tag'with'apostrophes") == "tag-with-apostrophes"
        assert sanitize_obsidian_tag("tag[with]brackets") == "tag-with-brackets"
        assert sanitize_obsidian_tag("tag{with}braces") == "tag-with-braces"
        assert sanitize_obsidian_tag("tag%with%percent") == "tag-with-percent"
        assert sanitize_obsidian_tag("tag*with*asterisks") == "tag-with-asterisks"
        assert sanitize_obsidian_tag("tag+with+plus") == "tag-with-plus"
        assert sanitize_obsidian_tag("tag=with=equals") == "tag-with-equals"
        assert sanitize_obsidian_tag("tag\\with\\backslashes") == "tag-with-backslashes"

    def test_unicode_characters_preserved(self):
        """Test that working Unicode characters are preserved"""
        assert sanitize_obsidian_tag("tag€with€euro") == "tag€with€euro"
        assert sanitize_obsidian_tag("tag£with£pound") == "tag£with£pound"
        assert sanitize_obsidian_tag("tag¥with¥yen") == "tag¥with¥yen"
        assert sanitize_obsidian_tag("tag¿with¿inverted") == "tag¿with¿inverted"

    def test_forward_slashes_preserved(self):
        """Test that forward slashes are preserved (common in hierarchical tags)"""
        assert sanitize_obsidian_tag("category/subcategory") == "category/subcategory"
        assert sanitize_obsidian_tag("project/phase1/task") == "project/phase1/task"

    def test_numbers_at_start_prefixed(self):
        """Test that tags starting with numbers get prefixed"""
        assert sanitize_obsidian_tag("123") == "tag-123"
        assert sanitize_obsidian_tag("1st-place") == "tag-1st-place"
        assert sanitize_obsidian_tag("2024-goals") == "tag-2024-goals"

    def test_dash_cleanup(self):
        """Test that consecutive dashes are collapsed and leading/trailing dashes removed"""
        assert sanitize_obsidian_tag("tag--with--double--dashes") == "tag-with-double-dashes"
        assert sanitize_obsidian_tag("-leading-dash") == "leading-dash"
        assert sanitize_obsidian_tag("trailing-dash-") == "trailing-dash"
        assert sanitize_obsidian_tag("--multiple--leading--") == "multiple-leading"

    def test_complex_edge_cases(self):
        """Test complex real-world edge cases"""
        assert sanitize_obsidian_tag("complex-tag.with@multiple&symbols!") == "complex-tag-with-multiple-symbols"
        assert sanitize_obsidian_tag("tag with spaces and-symbols") == "tag-with-spaces-and-symbols"
        assert sanitize_obsidian_tag("€£¥•mixed¿currency!symbols?") == "tag-€£¥-mixed¿currency-symbols"

    def test_problematic_characters(self):
        """Test characters that cause parsing issues"""
        assert sanitize_obsidian_tag("tag:with:colons") == "tag-with-colons"
        assert sanitize_obsidian_tag("tag|with|pipes") == "tag-with-pipes"
        assert sanitize_obsidian_tag("tag^with^carets") == "tag-with-carets"
        assert sanitize_obsidian_tag("tag~with~tildes") == "tag-with-tildes"
        assert sanitize_obsidian_tag("tag`with`backticks") == "tag-with-backticks"

    def test_empty_and_minimal_cases(self):
        """Test empty and minimal input cases"""
        assert sanitize_obsidian_tag("") == ""  # Empty stays empty
        assert sanitize_obsidian_tag("#") == "invalid-tag"  # Only hash becomes invalid-tag
        assert sanitize_obsidian_tag("##") == "invalid-tag"  # Multiple hashes become invalid-tag
        assert sanitize_obsidian_tag("a") == "a"
        assert sanitize_obsidian_tag("#a") == "a"

    def test_unicode_text(self):
        """Test Unicode text (accented characters work in Obsidian)"""
        assert sanitize_obsidian_tag("café") == "café"
        assert sanitize_obsidian_tag("naïve") == "naïve"
        assert sanitize_obsidian_tag("résumé") == "résumé"

    def test_emoji_handling(self):
        """Test emoji handling (likely to be replaced)"""
        assert sanitize_obsidian_tag("🏷️tag") == "tag"  # Emoji gets replaced, then cleaned up

    def test_only_special_characters(self):
        """Test tags that are only special characters"""
        assert sanitize_obsidian_tag("!!!") == "invalid-tag"  # All symbols become invalid-tag
        assert sanitize_obsidian_tag("$$$") == "invalid-tag"
        assert sanitize_obsidian_tag("@@@") == "invalid-tag"

    def test_preserve_internal_structure(self):
        """Test that internal structure with valid characters is preserved"""
        assert sanitize_obsidian_tag("project_2024-Q1_phase-1") == "project_2024-Q1_phase-1"
        assert sanitize_obsidian_tag("team/frontend/bug-123") == "team/frontend/bug-123"