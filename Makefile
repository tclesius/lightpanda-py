BUMP ?= patch

.PHONY: release
release:
	uv version --no-sync --bump $(BUMP)
	git commit -am "Bump version to $$(uv version --short)"
	git tag -a "$$(uv version --short)" -m "$$(uv version --short)"
	git push --follow-tags
	gh release create "$$(uv version --short)" --generate-notes
