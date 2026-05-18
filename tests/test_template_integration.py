"""Integration tests: render_template_file with a real vault."""

import json
import pytest
from pathlib import Path

from envault.store import save_secrets
from envault.template import render_template_file, TemplateError


@pytest.fixture()
def vault_base(tmp_path):
    """Return a tmp dir with a pre-populated vault."""
    secrets = {"APP_HOST": "127.0.0.1", "APP_PORT": "8080", "SECRET_KEY": "topsecret"}
    save_secrets("myapp", secrets, "pass123", base_dir=tmp_path)
    return tmp_path


@pytest.fixture()
def template_file(tmp_path):
    content = "host={{ APP_HOST }}\nport={{ APP_PORT }}\nkey={{ SECRET_KEY }}\n"
    p = tmp_path / "app.conf.tmpl"
    p.write_text(content)
    return p


def test_render_creates_output_file(vault_base, template_file, tmp_path):
    from envault.store import load_secrets
    secrets = load_secrets("myapp", "pass123", base_dir=vault_base)
    out = tmp_path / "app.conf"
    render_template_file(template_file, out, secrets)
    assert out.exists()


def test_render_correct_values(vault_base, template_file, tmp_path):
    from envault.store import load_secrets
    secrets = load_secrets("myapp", "pass123", base_dir=vault_base)
    out = tmp_path / "app.conf"
    result = render_template_file(template_file, out, secrets)
    text = out.read_text()
    assert "host=127.0.0.1" in text
    assert "port=8080" in text
    assert "key=topsecret" in text
    assert set(result.resolved) == {"APP_HOST", "APP_PORT", "SECRET_KEY"}


def test_render_missing_key_non_strict(tmp_path):
    tmpl = tmp_path / "t.tmpl"
    tmpl.write_text("value={{ UNKNOWN }}")
    out = tmp_path / "t.out"
    result = render_template_file(tmpl, out, {}, strict=False)
    assert "{{ UNKNOWN }}" in out.read_text()
    assert "UNKNOWN" in result.missing


def test_render_missing_key_strict_raises(tmp_path):
    tmpl = tmp_path / "t.tmpl"
    tmpl.write_text("value={{ UNKNOWN }}")
    out = tmp_path / "t.out"
    with pytest.raises(TemplateError):
        render_template_file(tmpl, out, {}, strict=True)


def test_render_nonexistent_template_raises(tmp_path):
    with pytest.raises(TemplateError, match="not found"):
        render_template_file(tmp_path / "ghost.tmpl", tmp_path / "out", {})
