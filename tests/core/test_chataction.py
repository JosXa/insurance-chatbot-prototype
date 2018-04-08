from core import ChatAction


def ca(text):
    return ChatAction(action_type=ChatAction.Type.SAYING, peer=None, text=text)


def test_remove_html():
    assert " Stripped away (http://google.com)" == ca("<a href='http://google.com'> Stripped away< /a>").render(
        remove_html=True)
    assert " Hi " == ca("<i> Hi < /i>").render(remove_html=True)
