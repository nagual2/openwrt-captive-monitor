from html.parser import HTMLParser
from urllib.parse import urljoin, urlparse, urlencode
from urllib.request import Request

class SimpleForm:
    def __init__(self, action="", method="GET"):
        self.action = action
        self.method = (method or "GET").upper()
        self.inputs = []

    def add_input(self, name, value):
        if name is not None:
            self.inputs.append((name, value or ""))

    def to_request(self, base_url):
        data = dict(self.inputs)
        if self.method == "GET":
            if self.action:
                target = urljoin(base_url, self.action)
            else:
                target = base_url
            parsed = urlparse(target)
            qs = urlencode(data)
            new_url = parsed._replace(query=qs).geturl()
            return Request(new_url, headers={"User-Agent": "nojs-agent/1.0"})
        else:
            if self.action:
                target = urljoin(base_url, self.action)
            else:
                target = base_url
            body = urlencode(data).encode("utf-8")
            req = Request(target, data=body, headers={
                "User-Agent": "nojs-agent/1.0",
                "Content-Type": "application/x-www-form-urlencoded"
            })
            return req

class FormParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.forms = []
        self._current = None

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag.lower() == "form":
            self._current = SimpleForm(
                action=attrs.get("action", ""),
                method=attrs.get("method", "GET"),
            )
        elif tag.lower() == "input" and self._current is not None:
            name = attrs.get("name")
            t = (attrs.get("type") or "text").lower()
            value = attrs.get("value", "")
            if t in ("checkbox", "radio"):
                if not value:
                    value = "1"
                self._current.add_input(name, value)
            else:
                self._current.add_input(name, value)
        elif tag.lower() == "button" and self._current is not None:
            name = attrs.get("name")
            value = attrs.get("value", "")
            if name:
                self._current.add_input(name, value or "1")

    def handle_endtag(self, tag):
        if tag.lower() == "form" and self._current is not None:
            self.forms.append(self._current)
            self._current = None

