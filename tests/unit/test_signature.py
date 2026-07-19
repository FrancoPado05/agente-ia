from src.webhook.signature import verify_meta_signature


def test_valid_signature():
    payload = b'{"test": "data"}'
    sig = "sha256=869276436102bf4dec269471ad3562c6cd2de6c57b0161e56d518ef494e477ae"
    assert verify_meta_signature(payload, sig, "mysecret")


def test_invalid_signature():
    payload = b'{"test": "data"}'
    assert not verify_meta_signature(payload, "sha256=invalid", "mysecret")
