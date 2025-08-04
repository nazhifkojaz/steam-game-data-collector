import pytest

class TestBaseSource:
    @pytest.mark.parametrize("selected_labels, valid_labels, expected", [
        # using default valid_labels (from fixture)
        (["test_label_1"], None, ["test_label_1"]),
        (["test_label_1", "invalid"], None, ["test_label_1"]),
        (["invalid"], None, []),
        
        # using custom valid_labels parameter
        (["custom_1"], ["custom_1", "custom_2"], ["custom_1"]),
        (["custom_1", "invalid"], ["custom_1", "custom_2"], ["custom_1"]),
        (["invalid"], ["custom_1"], []),
        
        # empty and all
        ([], None, []),
        (["test_label_1", "test_label_2"], None, ["test_label_1", "test_label_2"]),
    ])
    def test_filter_valid_labels(self, base_source_fixture, selected_labels, valid_labels, expected):
        """Test label filtering with various combinations"""
        if valid_labels is not None:
            result = base_source_fixture._filter_valid_labels(
                selected_labels=selected_labels,
                valid_labels=valid_labels
            )
        else:
            result = base_source_fixture._filter_valid_labels(
                selected_labels=selected_labels
            )
        
        assert isinstance(result, list)
        assert result == expected