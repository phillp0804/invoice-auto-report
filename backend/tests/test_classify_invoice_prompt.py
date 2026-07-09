"""分類 Prompt 模板的單元測試。"""

from services.prompts.classify_invoice_prompt import build_classify_invoice_system_prompt


class TestBuildClassifyInvoiceSystemPrompt:
    """build_classify_invoice_system_prompt() 測試。"""

    def test_lists_every_given_category(self):
        prompt = build_classify_invoice_system_prompt(["餐飲", "交通", "其他"])

        assert "- 餐飲" in prompt
        assert "- 交通" in prompt
        assert "- 其他" in prompt

    def test_instructs_json_only_output(self):
        prompt = build_classify_invoice_system_prompt(["其他"])

        assert "JSON" in prompt
        assert "category" in prompt
