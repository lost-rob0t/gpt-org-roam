-- Small EPUB cleanup pass for standalone tutorial books.

function Link(element)
  -- Org-roam id: links point to nodes outside a standalone tutorial EPUB.
  -- Keep the human-readable label without shipping a broken URI.
  if element.target:match("^id:") then
    return element.content
  end
  return element
end

function CodeBlock(element)
  element.classes:insert("kindle-code")
  return element
end

function Image(element)
  if pandoc.utils.stringify(element.caption) == "" then
    local name = element.src:match("([^/]+)$") or "image"
    element.caption = {pandoc.Str(name)}
  end
  return element
end
