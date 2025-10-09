import commonforms
import formalpdf

def test_inference(tmp_path):
    # tmp_path is a built-in pythest fixture where we'll write the outputs
    output_path = tmp_path / "output.pdf"
    commonforms.prepare_form("./tests/resources/input.pdf", output_path) 

    assert output_path.exists()

    doc = formalpdf.open(output_path)
    assert len(doc[0].widgets()) > 0
    
    doc.document.close()
