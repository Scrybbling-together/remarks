# Contributing

## Engineering Principles

1. Preserve as much metadata as possible
   - When working with source PDFs, **always mutate existing pages**
   - Never create new pages when a source PDF exists
   - This preserves the original document structure and metadata
2. Code without a test is code that doesn't exist
   - When adding a new feature or fixing a bug, **always write a test _first_**
   - Tests in remarks have multiple purposes...
     - ... we write software for people: our tests document and verify end-user expectations
     - ... code is not the product: the software is, the code is meant to implement the executable specification 
     - ... reproducible examples on any computer: software is complex, so let's manage it one place
   - This makes sure we always have a very high-quality single-source of truth for decisions and expectations
   - Refer to the [testing document, testing.md](testing.md) for more information
