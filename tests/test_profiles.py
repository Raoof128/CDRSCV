import json

import pytest

from cdrcsv.profiles import load_profiles_from_file


def test_load_profiles_from_file_supports_json(tmp_path):
    profile_file = tmp_path / "profiles.json"
    profile_file.write_text(
        json.dumps(
            {
                "custom": {
                    "request": {"base_url": "https://example.com", "endpoint": "/foo"},
                    "expected_headers": [],
                    "response_expectations": {"status_codes": [200]},
                    "tls": {"min_version": "TLSv1.2", "allowed_cipher_substrings": ["AES"]},
                }
            }
        )
    )
    profiles = load_profiles_from_file(profile_file)
    assert "custom" in profiles


def test_load_profiles_from_file_validates_structure(tmp_path):
    bad_file = tmp_path / "bad.json"
    bad_file.write_text("[]")
    with pytest.raises(ValueError):
        load_profiles_from_file(bad_file)
