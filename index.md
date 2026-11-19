---
title: Cherri Fork V2
nav_exclude: true
search_exclude: false
layout: default
nav_order: 1
---

<div class="hero">
  <img src="{{ '/assets/cherri_icon.png' | relative_url }}" width="96" height="96" alt="Cherri"/>
  <h1>Write Apple Shortcuts with Cherri V2.</h1>
  <p>The active authoring guide for the davidpovarsky fork of Cherri.</p>
  <p><a id="start-authoring" href="{{ '/fork-language/guide' | relative_url }}" class="btn btn-red">Start with the V2 guide</a>
  <a href="{{ '/fork-language/actions' | relative_url }}" class="btn">Find an action</a></p>
</div>

## Your first program

Save this example as a `.cherri` file:

```cherri
let name = "Cherri"
show(f"Hello from {name}!")
```

The default compiler language is V2. The examples on this site are checked
against an immutable compiler revision before publication.

## Read the current documentation

- [Language guide]({{ '/fork-language/guide' | relative_url }}) — bindings, strings, types, functions, control flow, and diagnostics.
- [Action reference]({{ '/fork-language/actions' | relative_url }}) — generated native action signatures and separately identified compiler macros.
- [Migration guide]({{ '/fork-language/migration' | relative_url }}) — moving existing programs to V2.
- [Fork source and build instructions](https://github.com/davidpovarsky/cherri) — compiler, tests, and supported workflows.

A catalog entry describes compiler support; Apple runtime acceptance is
established separately. See each feature's documented constraints.

## Historical reference

The [reference archive]({{ '/language/' | relative_url }}) retains upstream
material and previously migrated pages. It is outside this site's default
search and navigation. Use the current guide above when writing new code.
Legacy compilation requires an explicit `--lang=legacy` selection.

Cherri originated in the [upstream project](https://github.com/electrikmilk/cherri).
This site documents the fork; upstream releases and tools may use different syntax.
