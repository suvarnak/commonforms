import commonforms
import commonforms.exceptions

import formalpdf
import pytest


def test_inference(tmp_path):
    # tmp_path is a built-in pythest fixture where we'll write the outputs
    output_path = tmp_path / "output.pdf"
    commonforms.prepare_form("./tests/resources/input.pdf", output_path)

    assert output_path.exists()

    doc = formalpdf.open(output_path)
    assert len(doc[0].widgets()) > 0

    doc.document.close()


def test_inference_fast(tmp_path):
    output_path = tmp_path / "output.pdf"
    commonforms.prepare_form("./tests/resources/input.pdf", output_path, fast=True)

    assert output_path.exists()

    doc = formalpdf.open(output_path)
    assert len(doc[0].widgets()) > 0

    doc.document.close()


def test_encrypted_failure(tmp_path):
    # Reminder to future Joe: password for encrypted PDF is "kanbanery"
    output_path = tmp_path / "output.pdf"

    with pytest.raises(commonforms.exceptions.EncryptedPdfError):
        commonforms.prepare_form("./tests/resources/encrypted.pdf", output_path)
