# translator_deep.py
"""
このモジュールは deep-translator を使用して翻訳機能を提供します。
他の Python モジュールから import して利用してください。
"""

from deep_translator import GoogleTranslator

def translate_text(text: str, src: str = 'en', dest: str = 'ja') -> str:
    """
    与えられたテキストを指定された言語から別の言語に翻訳します。

    :param text: 翻訳するテキスト
    :param src: 原文の言語コード (例: 'en')
    :param dest: 翻訳先の言語コード (例: 'ja')
    :return: 翻訳後のテキスト
    """
    try:
        translator = GoogleTranslator(source=src, target=dest)
        translated = translator.translate(text)
        return translated
    except Exception as e:
        raise RuntimeError(f"翻訳エラー: {e}")

# モジュール単体で動作確認したい場合のサンプル
if __name__ == '__main__':
    original_text = "Hello, world!"
    translated_text = translate_text(original_text, src='en', dest='ja')
    print("原文:", original_text)
    print("翻訳:", translated_text)
