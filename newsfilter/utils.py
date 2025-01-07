from bs4 import BeautifulSoup


def html_to_text(html: str) -> str:
    soup = BeautifulSoup(html, "html.parser")

    for element in soup(["script", "style"]):
        element.decompose()

    # Get text with a separator to preserve line breaks
    text = soup.get_text(separator="\n")

    # Break into lines and remove leading/trailing spaces
    lines = (line.strip() for line in text.splitlines())

    # Remove empty lines and join the text
    clean_text = "\n\n".join(line for line in lines if line)

    return clean_text
