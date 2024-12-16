# Notes on rendering

The digital technology powering the ReMarkable is a virtual canvas.

Its task is to reconcile four things 

1. Source documents
2. Display
3. Input 
4. annotation.

## Definitions

**Virtual canvas**

The virtual canvas is a software representation of a remarkable notebook.
It ensures that no matter the ingredients put into a ReMarkable notebook, it will render and function as expected.

**Source document**

A document format that the ReMarkable can read:

- PDF
- Epub
- Ebook
- ReMarkable Quick notes
- ReMarkable notebooks

**Display**

While the ReMarkable is a physical device, its documents can appear on various devices. Each device has different
resolution, physical dimensions and therefore pixel density.

- The ReMarkable 1
- The ReMarkable 2
- The ReMarkable Paper Pro
- Phones & tablets (through the ReMarkable app)
- Various other computers, laptops and desktops (through the ReMarkable software)

**Annotation**

An annotation is anything you add with the ReMarkable.

Think of

- Anything written with the tools
- Text written with the text tool
- Highlights

## The virtual canvas and the scene tree

So how does this all work? On the surface, it sounds simple.
But in practice? Definitely somewhat complex.

It does that, with a scene tree.