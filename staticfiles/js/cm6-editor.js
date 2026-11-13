/**
 * SkillSphere CodeMirror 6 Universal Engine
 * Phase 1 — Professional VS Code-Inspired Code Editor
 * 
 * Features:
 * - CodeMirror 6 with VS Code Dark syntax theme
 * - Line numbers, active line highlight, bracket matching & auto-closing
 * - Dynamic language switching (Python, JavaScript, SQL) via Compartment
 * - Auto-indent and tab key support (indentWithTab)
 * - Search & replace (Ctrl+F / Cmd+F), Undo / Redo (Ctrl+Z / Cmd+Z, Ctrl+Shift+Z)
 * - Shortcuts: Ctrl+Enter / Cmd+Enter triggers runCode
 * - Bidirectional sync with underlying textarea
 * - Zero-flicker collaborative setValue with cursor preservation
 * - Graceful textarea fallback if CDN / ESM is unavailable
 */

(function (window) {
    'use strict';

    // Pinned CDN endpoints for CodeMirror 6 packages
    const CM6_CDN = {
        core: 'https://cdn.jsdelivr.net/npm/codemirror@6.0.1/+esm',
        state: 'https://cdn.jsdelivr.net/npm/@codemirror/state@6.4.1/+esm',
        view: 'https://cdn.jsdelivr.net/npm/@codemirror/view@6.24.1/+esm',
        language: 'https://cdn.jsdelivr.net/npm/@codemirror/language@6.10.1/+esm',
        commands: 'https://cdn.jsdelivr.net/npm/@codemirror/commands@6.3.3/+esm',
        autocomplete: 'https://cdn.jsdelivr.net/npm/@codemirror/autocomplete@6.12.0/+esm',
        search: 'https://cdn.jsdelivr.net/npm/@codemirror/search@6.5.6/+esm',
        python: 'https://cdn.jsdelivr.net/npm/@codemirror/lang-python@6.1.6/+esm',
        javascript: 'https://cdn.jsdelivr.net/npm/@codemirror/lang-javascript@6.2.2/+esm',
        sql: 'https://cdn.jsdelivr.net/npm/@codemirror/lang-sql@6.8.0/+esm',
    };

    /**
     * Creates and mounts a CodeMirror 6 editor on a given textarea.
     * 
     * @param {Object} options
     * @param {string|HTMLTextAreaElement} options.target - Textarea element or its ID
     * @param {string|HTMLElement} options.container - Container element or its ID
     * @param {string} [options.language='python'] - 'python' | 'javascript' | 'sql'
     * @param {Function} [options.onRunCode] - Callback for Ctrl+Enter / Cmd+Enter
     * @param {Function} [options.onDocChange] - Callback when content changes
     * @returns {Promise<SkillSphereEditorInstance>}
     */
    async function createSkillSphereEditor(options) {
        const textarea = typeof options.target === 'string'
            ? document.getElementById(options.target)
            : options.target;

        const container = typeof options.container === 'string'
            ? document.getElementById(options.container)
            : options.container;

        if (!textarea || !container) {
            console.error('[CM6] Target textarea or container not found:', options);
            return null;
        }

        const initialCode = textarea.value || '';
        const initialLang = (options.language || 'python').toLowerCase();
        let fallbackNoticeEl = null;

        const showFallbackNotice = (msg) => {
            if (!container.querySelector('.cm6-fallback-banner')) {
                fallbackNoticeEl = document.createElement('div');
                fallbackNoticeEl.className = 'cm6-fallback-banner alert alert-warning d-flex align-items-center gap-2 p-2 m-2 small';
                fallbackNoticeEl.style.fontSize = '0.78rem';
                fallbackNoticeEl.innerHTML = `
                    <i data-lucide="alert-triangle" style="width:14px;height:14px;"></i>
                    <span><strong>Editor Fallback Active:</strong> ${msg || 'Advanced code editor offline. Standard editor is fully functional.'}</span>
                `;
                container.prepend(fallbackNoticeEl);
                if (window.lucide && typeof window.lucide.createIcons === 'function') {
                    window.lucide.createIcons();
                }
            }
            textarea.classList.remove('d-none');
            textarea.style.display = 'block';
        };

        try {
            // Dynamically import CodeMirror 6 ESM modules
            const [
                cmState,
                cmView,
                cmLang,
                cmCmd,
                cmAuto,
                cmSearch,
                pyLang,
                jsLang,
                sqlLang
            ] = await Promise.all([
                import(CM6_CDN.state),
                import(CM6_CDN.view),
                import(CM6_CDN.language),
                import(CM6_CDN.commands),
                import(CM6_CDN.autocomplete),
                import(CM6_CDN.search),
                import(CM6_CDN.python),
                import(CM6_CDN.javascript),
                import(CM6_CDN.sql)
            ]);

            const { EditorState, Compartment } = cmState;
            const { EditorView, keymap, lineNumbers, highlightActiveLine, highlightActiveLineGutter } = cmView;
            const { defaultHighlightStyle, syntaxHighlighting, bracketMatching, indentOnInput } = cmLang;
            const { defaultKeymap, history, historyKeymap, indentWithTab } = cmCmd;
            const { closeBrackets, closeBracketsKeymap } = cmAuto;
            const { searchKeymap, highlightSelectionMatches } = cmSearch;

            // Language loaders map
            const languageCompartment = new Compartment();
            const getLanguageExtension = (lang) => {
                switch (lang) {
                    case 'javascript':
                    case 'js':
                        return jsLang.javascript();
                    case 'sql':
                    case 'postgres':
                    case 'postgresql':
                        return sqlLang.sql();
                    case 'python':
                    case 'py':
                    default:
                        return pyLang.python();
                }
            };

            // VS Code Dark Theme Specification
            // Editor background: #1E1E1E, Gutter: #252526, Current line: #2A2D2E
            // Default text: #D4D4D4, Keywords: #569CD6, Strings: #CE9178, Functions: #DCDCAA
            // Comments: #6A9955, Numbers: #B5CEA8, Selection: #264F78
            const vsCodeDarkTheme = EditorView.theme({
                '&': {
                    color: '#D4D4D4',
                    backgroundColor: '#1E1E1E',
                    fontFamily: "'Fira Code', 'JetBrains Mono', 'Consolas', monospace",
                    fontSize: '14px',
                    height: '100%',
                    borderRadius: '8px',
                    overflow: 'hidden',
                },
                '.cm-content': {
                    caretColor: '#AEAFAD',
                    padding: '12px 0',
                    fontFamily: 'inherit',
                },
                '&.cm-focused .cm-cursor': {
                    borderLeftColor: '#AEAFAD',
                    borderLeftWidth: '2px',
                },
                '&.cm-focused .cm-selectionBackground, .cm-selectionBackground, .cm-content ::selection': {
                    backgroundColor: '#264F78 !important',
                },
                '.cm-activeLine': {
                    backgroundColor: '#2A2D2E',
                },
                '.cm-gutters': {
                    backgroundColor: '#252526',
                    color: '#858585',
                    borderRight: '1px solid rgba(255, 255, 255, 0.08)',
                    fontFamily: 'inherit',
                },
                '.cm-activeLineGutter': {
                    backgroundColor: '#2A2D2E',
                    color: '#C6C6C6',
                },
                '.cm-lineNumbers .cm-gutterElement': {
                    padding: '0 10px 0 12px',
                    minWidth: '36px',
                },
                '.cm-matchingBracket': {
                    backgroundColor: 'rgba(255, 255, 255, 0.15)',
                    outline: '1px solid #75715E',
                    color: '#FFFFFF !important',
                },
                '.cm-scroller': {
                    fontFamily: 'inherit',
                    lineHeight: '1.6',
                    overflow: 'auto',
                }
            }, { dark: true });

            // Custom keyboard shortcuts
            const customRunKeymap = keymap.of([
                {
                    key: 'Mod-Enter', // Ctrl-Enter on Windows/Linux, Cmd-Enter on Mac
                    run: () => {
                        if (typeof options.onRunCode === 'function') {
                            options.onRunCode();
                            return true;
                        }
                        return false;
                    }
                },
                indentWithTab
            ]);

            // Document update listener to sync with hidden textarea
            let suppressSync = false;
            const syncExtension = EditorView.updateListener.of((update) => {
                if (update.docChanged && !suppressSync) {
                    const newText = update.state.doc.toString();
                    textarea.value = newText;
                    if (typeof options.onDocChange === 'function') {
                        options.onDocChange(newText);
                    }
                }
            });

            // Create Initial EditorState
            const startState = EditorState.create({
                doc: initialCode,
                extensions: [
                    lineNumbers(),
                    highlightActiveLineGutter(),
                    highlightActiveLine(),
                    history(),
                    bracketMatching(),
                    closeBrackets(),
                    indentOnInput(),
                    highlightSelectionMatches(),
                    languageCompartment.of(getLanguageExtension(initialLang)),
                    vsCodeDarkTheme,
                    syntaxHighlighting(defaultHighlightStyle, { fallback: true }),
                    customRunKeymap,
                    keymap.of([
                        ...closeBracketsKeymap,
                        ...defaultKeymap,
                        ...searchKeymap,
                        ...historyKeymap
                    ]),
                    syncExtension,
                    EditorView.lineWrapping
                ]
            });

            // Mount EditorView in container
            const editorView = new EditorView({
                state: startState,
                parent: container
            });

            // Hide the original textarea safely
            textarea.classList.add('d-none');
            textarea.style.display = 'none';

            // Public instance wrapper
            const instance = {
                view: editorView,
                isFallback: false,

                /**
                 * Retrieve current code from the editor
                 */
                getValue: () => editorView.state.doc.toString(),

                /**
                 * Update code content while preserving cursor and preventing infinite sync loops
                 * @param {string} newText
                 * @param {boolean} [preserveCursor=false]
                 */
                setValue: (newText, preserveCursor = false) => {
                    if (newText === undefined || newText === null) return;
                    const current = editorView.state.doc.toString();
                    if (current === newText) return; // Prevent unnecessary re-renders & infinite loop

                    suppressSync = true;
                    try {
                        const currentSelection = editorView.state.selection.main;
                        const len = newText.length;
                        const safeAnchor = Math.min(currentSelection.anchor, len);
                        const safeHead = Math.min(currentSelection.head, len);

                        editorView.dispatch({
                            changes: { from: 0, to: current.length, insert: newText },
                            selection: preserveCursor ? { anchor: safeAnchor, head: safeHead } : undefined
                        });
                        textarea.value = newText;
                    } finally {
                        suppressSync = false;
                    }
                },

                /**
                 * Dynamically switch programming language
                 * @param {string} lang - 'python' | 'javascript' | 'sql'
                 */
                setLanguage: (lang) => {
                    const ext = getLanguageExtension(lang);
                    editorView.dispatch({
                        effects: languageCompartment.reconfigure(ext)
                    });
                },

                /**
                 * Focus editor
                 */
                focus: () => editorView.focus(),

                /**
                 * Destroy editor instance and restore textarea
                 */
                destroy: () => {
                    editorView.destroy();
                    textarea.classList.remove('d-none');
                    textarea.style.display = 'block';
                }
            };

            return instance;

        } catch (err) {
            console.warn('[CM6] Failed to initialize CodeMirror 6:', err);
            showFallbackNotice(err.message);

            // Return graceful fallback object wrapping original textarea
            return {
                view: null,
                isFallback: true,
                getValue: () => textarea.value,
                setValue: (newText) => { textarea.value = newText; },
                setLanguage: () => {},
                focus: () => textarea.focus(),
                destroy: () => {}
            };
        }
    }

    // Export to global scope
    window.SkillSphereCodeEditor = {
        create: createSkillSphereEditor
    };

})(window);
