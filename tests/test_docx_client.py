"""Tests for the DocxExporter class in src/docx_client.py."""

from unittest.mock import MagicMock, patch

from src.docx_client import DocxExporter


def make_entity(type_name: str, offset: int, length: int, url: str | None = None):
    entity = type(type_name, (), {})()
    entity.offset = offset
    entity.length = length
    if url is not None:
        entity.url = url
    return entity


@patch("src.docx_client.Document")
def test_docx_exporter_init(mock_doc_class):
    """Test the initialization of DocxExporter."""
    mock_doc_class.return_value.styles = {"Normal": MagicMock()}
    exporter = DocxExporter()
    assert exporter.doc == mock_doc_class.return_value
    assert exporter.doc.styles["Normal"].font.name == "Calibri"


@patch("src.docx_client.add_hyperlink")
@patch("src.docx_client.Document")
def test_add_formatted_text(mock_doc_class, mock_add_hyperlink):
    """Test that text formatting is applied correctly based on entities."""
    # This mock is crucial to prevent the TypeError in lxml
    mock_doc_class.return_value.add_paragraph.return_value.part.relate_to.return_value = "rId1"

    exporter = DocxExporter()
    paragraph_mock = exporter.doc.add_paragraph.return_value

    text = "bold italic link"
    entities = [
        make_entity("MessageEntityBold", 0, 4),
        make_entity("MessageEntityItalic", 5, 6),
        make_entity("MessageEntityTextUrl", 12, 4, url="http://example.com"),
    ]
    exporter._add_formatted_text(text, entities)

    assert paragraph_mock.add_run.call_count == 4
    mock_add_hyperlink.assert_called_once()


@patch("src.docx_client.Document")
def test_add_formatted_text_no_entities_adds_plain_paragraph(mock_doc_class):
    """Test that when no entities are provided, plain text paragraph is added."""
    exporter = DocxExporter()

    exporter._add_formatted_text("plain", [])

    exporter.doc.add_paragraph.assert_called_once_with("plain")


@patch("src.docx_client.add_hyperlink")
@patch("src.docx_client.Document")
def test_add_formatted_text_url_entity_prepends_scheme(mock_doc_class, mock_add_hyperlink):
    """Test that MessageEntityUrl auto-prepends https:// when missing."""
    mock_doc_class.return_value.add_paragraph.return_value.part.relate_to.return_value = "rId1"

    exporter = DocxExporter(hyperlink_handling="active")
    paragraph_mock = exporter.doc.add_paragraph.return_value

    exporter._add_formatted_text("example.com", [make_entity("MessageEntityUrl", 0, 11)])

    mock_add_hyperlink.assert_called_once_with(paragraph_mock, "https://example.com", "example.com")


@patch("src.docx_client.Document")
def test_add_formatted_text_code_entity_sets_font(mock_doc_class):
    """Test that code entity sets Courier New font on the created run."""
    exporter = DocxExporter()
    run_mock = MagicMock()
    run_mock.font = MagicMock()
    paragraph_mock = exporter.doc.add_paragraph.return_value
    paragraph_mock.add_run.return_value = run_mock

    exporter._add_formatted_text("code", [make_entity("MessageEntityCode", 0, 4)])

    assert run_mock.font.name == "Courier New"


@patch("src.docx_client.Document")
def test_add_formatted_text_sets_italic(mock_doc_class):
    """Test that italic entity sets `run.italic = True` on the created run."""
    exporter = DocxExporter()
    run_mock = MagicMock()
    paragraph_mock = exporter.doc.add_paragraph.return_value
    paragraph_mock.add_run.return_value = run_mock

    exporter._add_formatted_text("hello", [make_entity("MessageEntityItalic", 0, 5)])

    paragraph_mock.add_run.assert_called_once_with("hello")
    assert run_mock.italic is True


@patch("src.docx_client.add_hyperlink")
@patch("src.docx_client.Document")
def test_add_formatted_text_ignores_links(mock_doc_class, mock_add_hyperlink):
    """Test that `hyperlink_handling='ignore'` does not create active hyperlinks."""
    exporter = DocxExporter(hyperlink_handling="ignore")
    run_mock = MagicMock()
    paragraph_mock = exporter.doc.add_paragraph.return_value
    paragraph_mock.add_run.return_value = run_mock

    text = "link"
    entities = [make_entity("MessageEntityTextUrl", 0, 4, url="http://example.com")]
    exporter._add_formatted_text(text, entities)

    mock_add_hyperlink.assert_not_called()
    paragraph_mock.add_run.assert_called_once_with("link")
    assert run_mock.underline is True


@patch("src.docx_client.Image.open")

@patch("pathlib.Path.exists", return_value=True)
@patch("src.docx_client.Document")
def test_process_media_file_image(mock_doc_class, mock_path_exists, mock_image_open):
    """Test that supported image files are processed correctly."""
    exporter = DocxExporter()
    exporter._add_image = MagicMock()
    exporter._process_media_file("/fake/path/image.png")
    exporter._add_image.assert_called_once_with("/fake/path/image.png")


@patch("pathlib.Path.exists", return_value=False)
@patch("src.docx_client.Document")
def test_process_media_file_missing_is_noop(mock_doc_class, mock_path_exists):
    """Test that non-existent media files are ignored."""
    exporter = DocxExporter()
    exporter._add_image = MagicMock()

    exporter._process_media_file("/fake/path/missing.png")

    exporter._add_image.assert_not_called()
    exporter.doc.add_paragraph.assert_not_called()


@patch("src.docx_client.Document")
def test_process_media_file_unsupported(mock_doc_class):
    """Test that unsupported files result in a placeholder text."""
    exporter = DocxExporter()
    exporter._add_image = MagicMock()

    paragraph_mock = exporter.doc.add_paragraph.return_value
    run_mock = MagicMock()
    run_mock.font = MagicMock()
    run_mock.font.color = MagicMock()
    paragraph_mock.add_run.return_value = run_mock

    with patch("pathlib.Path.exists", return_value=True):
        exporter._process_media_file("/fake/path/video.mp4")

    exporter._add_image.assert_not_called()
    paragraph_mock.add_run.assert_called_once_with("[Unsupported file downloaded: video.mp4]")
    assert run_mock.italic is True
    run_mock.font.color.rgb = MagicMock()


@patch("pathlib.Path.exists", return_value=True)
@patch("src.docx_client.logging")
@patch("src.docx_client.Document")
def test_process_media_file_image_error_is_logged(mock_doc_class, mock_logging, mock_path_exists):
    """Test that image insertion errors are logged and do not propagate."""
    exporter = DocxExporter()
    exporter._add_image = MagicMock(side_effect=RuntimeError("boom"))

    exporter._process_media_file("/fake/path/image.png")

    mock_logging.error.assert_called_once()


@patch("src.docx_client.Document")
def test_save(mock_doc_class):
    """Test that the save method is called on the document object."""
    exporter = DocxExporter()
    exporter.save("test.docx")
    exporter.doc.save.assert_called_once_with("test.docx")


@patch("src.docx_client.Document")
def test_add_post_includes_heading_by_default(mock_doc_class):
    """Test that add_post adds a heading when include_date_heading=True."""
    exporter = DocxExporter(include_date_heading=True)
    exporter._add_formatted_text = MagicMock()
    exporter._process_media_file = MagicMock()

    exporter.add_post(
        date=MagicMock(strftime=MagicMock(return_value="Jan 01, 2024")),
        text="hello",
        images=[],
        entities=[],
    )

    exporter.doc.add_heading.assert_called_once_with("Jan 01, 2024", level=2)
    exporter._add_formatted_text.assert_called_once_with("hello", [])


@patch("src.docx_client.Document")
def test_add_post_skips_heading_when_disabled(mock_doc_class):
    """Test that add_post does not add a heading when include_date_heading=False."""
    exporter = DocxExporter(include_date_heading=False)
    exporter._add_formatted_text = MagicMock()
    exporter._process_media_file = MagicMock()

    exporter.add_post(
        date=MagicMock(),
        text="hello",
        images=[],
        entities=[],
    )

    exporter.doc.add_heading.assert_not_called()
    exporter._add_formatted_text.assert_called_once_with("hello", [])


@patch("src.docx_client.Document")
def test_add_post_image_position_before_calls_process_before_text(mock_doc_class):
    """Test that images are processed before text when image_position='before'."""
    exporter = DocxExporter(image_position="before")
    call_log: list[tuple[str, str]] = []

    def process_side_effect(path: str) -> None:
        call_log.append(("image", path))

    def text_side_effect(text: str, entities: list) -> None:
        call_log.append(("text", text))

    exporter._process_media_file = MagicMock(side_effect=process_side_effect)
    exporter._add_formatted_text = MagicMock(side_effect=text_side_effect)

    exporter.add_post(
        date=MagicMock(strftime=MagicMock(return_value="Jan 01, 2024")),
        text="hello",
        images=["a.png", "b.png"],
        entities=[],
    )

    assert call_log[:3] == [("image", "a.png"), ("image", "b.png"), ("text", "hello")]


@patch("src.docx_client.Document")
def test_add_post_image_position_after_calls_process_after_text(mock_doc_class):
    """Test that images are processed after text when image_position='after'."""
    exporter = DocxExporter(image_position="after")
    call_log: list[tuple[str, str]] = []

    def process_side_effect(path: str) -> None:
        call_log.append(("image", path))

    def text_side_effect(text: str, entities: list) -> None:
        call_log.append(("text", text))

    exporter._process_media_file = MagicMock(side_effect=process_side_effect)
    exporter._add_formatted_text = MagicMock(side_effect=text_side_effect)

    exporter.add_post(
        date=MagicMock(strftime=MagicMock(return_value="Jan 01, 2024")),
        text="hello",
        images=["a.png"],
        entities=[],
    )

    assert call_log[:2] == [("text", "hello"), ("image", "a.png")]


@patch("src.docx_client.Image.open")
@patch("src.docx_client.Inches")
@patch("src.docx_client.Document")
def test_add_image_centers_and_sets_width(mock_doc_class, mock_inches, mock_image_open):
    """Test that _add_image centers the paragraph and uses a fixed width."""
    img_ctx = MagicMock()
    img_ctx.__enter__.return_value.size = (200, 100)
    mock_image_open.return_value = img_ctx
    mock_inches.return_value = "six_in"

    exporter = DocxExporter()
    paragraph_mock = exporter.doc.add_paragraph.return_value
    run_mock = paragraph_mock.add_run.return_value

    exporter._add_image("/fake/path/image.png")

    assert paragraph_mock.alignment is not None
    run_mock.add_picture.assert_called_once_with("/fake/path/image.png", width="six_in")

