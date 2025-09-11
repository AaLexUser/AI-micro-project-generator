import React, { useState, useRef, useEffect, useCallback } from 'react';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger } from '@/components/ui/dropdown-menu';
import { ChevronDown, Code, Sun, Moon } from 'lucide-react';

interface CodeEditorProps {
  value: string;
  onChange: (value: string) => void;
  placeholder?: string;
  className?: string;
  language?: string;
  onLanguageChange?: (language: string) => void;
  onKeyPress?: (e: React.KeyboardEvent) => void;
}

const SUPPORTED_LANGUAGES = [
  { value: 'javascript', label: 'JavaScript', extension: 'js' },
  { value: 'typescript', label: 'TypeScript', extension: 'ts' },
  { value: 'python', label: 'Python', extension: 'py' },
  { value: 'java', label: 'Java', extension: 'java' },
  { value: 'cpp', label: 'C++', extension: 'cpp' },
  { value: 'c', label: 'C', extension: 'c' },
  { value: 'csharp', label: 'C#', extension: 'cs' },
  { value: 'go', label: 'Go', extension: 'go' },
  { value: 'rust', label: 'Rust', extension: 'rs' },
  { value: 'php', label: 'PHP', extension: 'php' },
  { value: 'ruby', label: 'Ruby', extension: 'rb' },
  { value: 'swift', label: 'Swift', extension: 'swift' },
  { value: 'kotlin', label: 'Kotlin', extension: 'kt' },
  { value: 'sql', label: 'SQL', extension: 'sql' },
  { value: 'html', label: 'HTML', extension: 'html' },
  { value: 'css', label: 'CSS', extension: 'css' },
  { value: 'json', label: 'JSON', extension: 'json' },
  { value: 'xml', label: 'XML', extension: 'xml' },
  { value: 'yaml', label: 'YAML', extension: 'yaml' },
  { value: 'markdown', label: 'Markdown', extension: 'md' },
  { value: 'bash', label: 'Bash', extension: 'sh' },
  { value: 'plaintext', label: 'Plain Text', extension: 'txt' },
];

// Syntax highlighting themes
const THEMES = {
  light: {
    background: '#ffffff',
    default: '#1f2937',
    comment: '#6b7280',
    keyword: '#E67145',
    string: '#059669',
    number: '#0891b2',
    function: '#7c3aed',
    type: '#dc2626',
    operator: '#E67145',
    punctuation: '#6b7280',
    selection: 'rgba(230, 113, 69, 0.2)',
  },
  dark: {
    background: '#0f172a',
    default: '#e2e8f0',
    comment: '#64748b',
    keyword: '#E67145',
    string: '#34d399',
    number: '#38bdf8',
    function: '#a78bfa',
    type: '#f87171',
    operator: '#E67145',
    punctuation: '#94a3b8',
    selection: 'rgba(230, 113, 69, 0.3)',
  },
};

// Token types for syntax highlighting
const TOKEN_REGEX = {
  javascript: {
    comment: /(\/\/.*$|\/\*[\s\S]*?\*\/)/gm,
    string: /(["'`])(?:(?=(\\?))\2.)*?\1/g,
    keyword: /\b(const|let|var|function|return|if|else|for|while|do|switch|case|break|continue|try|catch|finally|throw|new|typeof|instanceof|in|of|class|extends|constructor|super|static|async|await|yield|import|export|default|from|as)\b/g,
    number: /\b(\d+\.?\d*|0x[0-9a-fA-F]+)\b/g,
    function: /\b([a-zA-Z_$][a-zA-Z0-9_$]*)\s*(?=\()/g,
    operator: /([+\-*/%=<>!&|^~?:]|&&|\|\||==|!=|===|!==|<=|>=|\+\+|--|=>)/g,
    punctuation: /[{}[\];(),]/g,
  },
  python: {
    comment: /(#.*$)/gm,
    string: /(["']{1,3})(?:(?=(\\?))\2.)*?\1/g,
    keyword: /\b(def|class|if|elif|else|for|while|return|import|from|as|try|except|finally|with|lambda|yield|global|nonlocal|pass|break|continue|raise|assert|del|in|is|not|and|or|True|False|None)\b/g,
    number: /\b(\d+\.?\d*|0x[0-9a-fA-F]+)\b/g,
    function: /\b([a-zA-Z_][a-zA-Z0-9_]*)\s*(?=\()/g,
    operator: /([+\-*/%=<>!&|^~:]|==|!=|<=|>=|\/\/|\*\*|@)/g,
    punctuation: /[{}[\];(),]/g,
  },
};

// Syntax highlighter function
const highlightCode = (code: string, language: string, theme: typeof THEMES.light): string => {
  const rules = TOKEN_REGEX[language as keyof typeof TOKEN_REGEX] || TOKEN_REGEX.javascript;

  // Store all tokens with their positions
  const tokens: Array<{ type: string; value: string; start: number; end: number }> = [];

  // Extract all tokens
  Object.entries(rules).forEach(([type, regex]) => {
    const matches = [...code.matchAll(new RegExp(regex.source, regex.flags))];
    matches.forEach(match => {
      if (match.index !== undefined) {
        tokens.push({
          type,
          value: match[0],
          start: match.index,
          end: match.index + match[0].length,
        });
      }
    });
  });

  // Sort tokens by position
  tokens.sort((a, b) => a.start - b.start);

  // Build highlighted HTML
  let result = '';
  let lastEnd = 0;

  tokens.forEach(token => {
    // Add any unhighlighted text before this token
    if (token.start > lastEnd) {
      result += `<span style="color: ${theme.default}">${escapeHtml(code.slice(lastEnd, token.start))}</span>`;
    }

    // Add the highlighted token
    const color = theme[token.type as keyof typeof theme] || theme.default;
    result += `<span style="color: ${color}">${escapeHtml(token.value)}</span>`;

    lastEnd = token.end;
  });

  // Add any remaining text
  if (lastEnd < code.length) {
    result += `<span style="color: ${theme.default}">${escapeHtml(code.slice(lastEnd))}</span>`;
  }

  return result || `<span style="color: ${theme.default}">${escapeHtml(code)}</span>`;
};

const escapeHtml = (text: string): string => {
  const div = document.createElement('div');
  div.textContent = text;
  return div.innerHTML;
};

export function CodeEditor({
  value,
  onChange,
  placeholder = "Write your code here...",
  className = "",
  language = "javascript",
  onLanguageChange,
  onKeyPress
}: CodeEditorProps) {
  const [isDarkMode, setIsDarkMode] = useState(true);
  const [selectedLanguage, setSelectedLanguage] = useState(language);
  const editorRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const highlightRef = useRef<HTMLDivElement>(null);
  const lineNumbersRef = useRef<HTMLDivElement>(null);

  const theme = isDarkMode ? THEMES.dark : THEMES.light;
  const currentLanguage = SUPPORTED_LANGUAGES.find(lang => lang.value === selectedLanguage) || SUPPORTED_LANGUAGES[0];

  // Fixed monospace font settings
  const fontFamily = 'Monaco, Menlo, "Ubuntu Mono", Consolas, "Courier New", monospace';
  const fontSize = '14px';
  const lineHeight = '21px';

  useEffect(() => {
    setSelectedLanguage(language);
  }, [language]);

  // Sync scroll between textarea and highlight layer
  const handleScroll = useCallback((e: React.UIEvent<HTMLTextAreaElement>) => {
    if (highlightRef.current && lineNumbersRef.current) {
      highlightRef.current.scrollTop = e.currentTarget.scrollTop;
      highlightRef.current.scrollLeft = e.currentTarget.scrollLeft;
      lineNumbersRef.current.scrollTop = e.currentTarget.scrollTop;
    }
  }, []);

  const handleChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    onChange(e.target.value);
  };

  const handleLanguageChange = (newLanguage: string) => {
    setSelectedLanguage(newLanguage);
    onLanguageChange?.(newLanguage);
  };

  // Update highlighted code
  const highlightedCode = highlightCode(value || placeholder, selectedLanguage, theme);
  const lines = (value || placeholder).split('\n');
  const lineCount = lines.length;

  // Calculate editor dimensions
  const minHeight = 300;
  const maxHeight = 600;
  const editorHeight = Math.min(maxHeight, Math.max(minHeight, lineCount * 21 + 32));

  return (
    <div className={`relative overflow-hidden rounded-lg border ${isDarkMode ? 'border-gray-700 bg-[#0f172a]' : 'border-gray-300 bg-white'} ${className}`}>
      {/* Toolbar */}
      <div className={`flex items-center justify-between px-4 py-2 border-b ${isDarkMode ? 'bg-[#1e293b] border-gray-700' : 'bg-gray-50 border-gray-200'}`}>
        <div className="flex items-center gap-3">
          <Code className="w-4 h-4" style={{ color: '#E67145' }} />
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button
                variant="outline"
                size="sm"
                className="h-7 text-xs"
                style={{ borderColor: '#E67145', color: isDarkMode ? '#e2e8f0' : '#1f2937' }}
              >
                <Badge
                  variant="secondary"
                  className="mr-2 text-xs"
                  style={{ backgroundColor: 'rgba(230, 113, 69, 0.1)', color: '#E67145', borderColor: 'rgba(230, 113, 69, 0.2)' }}
                >
                  {currentLanguage.label}
                </Badge>
                <ChevronDown className="w-3 h-3" />
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent className="w-56 max-h-80 overflow-y-auto">
              {SUPPORTED_LANGUAGES.map((lang) => (
                <DropdownMenuItem
                  key={lang.value}
                  onClick={() => handleLanguageChange(lang.value)}
                  className={`flex items-center justify-between ${lang.value === selectedLanguage ? 'bg-[#E67145]/10' : ''}`}
                >
                  <span>{lang.label}</span>
                  <Badge
                    variant="outline"
                    className="text-xs"
                    style={{
                      borderColor: lang.value === selectedLanguage ? '#E67145' : undefined,
                      color: lang.value === selectedLanguage ? '#E67145' : undefined
                    }}
                  >
                    .{lang.extension}
                  </Badge>
                </DropdownMenuItem>
              ))}
            </DropdownMenuContent>
          </DropdownMenu>
        </div>

        <Button
          variant="ghost"
          size="sm"
          onClick={() => setIsDarkMode(!isDarkMode)}
          className="h-7 w-7 p-0"
          style={{ color: '#E67145' }}
        >
          {isDarkMode ? <Sun className="w-4 h-4" /> : <Moon className="w-4 h-4" />}
        </Button>
      </div>

      {/* Editor Container */}
      <div
        ref={editorRef}
        className="relative flex"
        style={{ height: `${editorHeight}px` }}
      >
        {/* Line Numbers */}
        <div
          ref={lineNumbersRef}
          className="select-none overflow-hidden"
          style={{
            paddingTop: '16px',
            paddingBottom: '16px',
            paddingRight: '12px',
            paddingLeft: '16px',
            fontFamily,
            fontSize,
            lineHeight,
            color: isDarkMode ? '#64748b' : '#9ca3af',
            backgroundColor: isDarkMode ? '#0f172a' : '#ffffff',
            borderRight: `1px solid ${isDarkMode ? '#334155' : '#e5e7eb'}`,
            minWidth: '50px',
            textAlign: 'right',
          }}
        >
          {lines.map((_, i) => (
            <div key={i} style={{ height: lineHeight }}>{i + 1}</div>
          ))}
        </div>

        {/* Code Container */}
        <div className="relative flex-1 overflow-hidden">
          {/* Syntax Highlighted Layer */}
          <div
            ref={highlightRef}
            className="absolute inset-0 overflow-auto pointer-events-none"
            style={{
              padding: '16px',
              fontFamily,
              fontSize,
              lineHeight,
              whiteSpace: 'pre',
              wordWrap: 'normal',
              overflowWrap: 'normal',
              scrollbarWidth: 'none',
              msOverflowStyle: 'none',
            } as React.CSSProperties}
            dangerouslySetInnerHTML={{ __html: highlightedCode }}
          />

          {/* Textarea Layer */}
          <textarea
            ref={textareaRef}
            value={value}
            onChange={handleChange}
            onScroll={handleScroll}
            onKeyPress={onKeyPress}
            placeholder={placeholder}
            className="absolute inset-0 bg-transparent resize-none outline-none"
            style={{
              padding: '16px',
              fontFamily,
              fontSize,
              lineHeight,
              color: 'transparent',
              caretColor: '#E67145',
              whiteSpace: 'pre',
              wordWrap: 'normal',
              overflowWrap: 'normal',
              overflowX: 'auto',
              overflowY: 'auto',
              scrollbarWidth: 'thin',
              scrollbarColor: isDarkMode ? '#475569 #1e293b' : '#cbd5e1 #f3f4f6',
            }}
            spellCheck={false}
            autoComplete="off"
            autoCorrect="off"
            autoCapitalize="off"
          />
        </div>
      </div>

      {/* Custom Scrollbar Styles */}
      <style>{`
        /* Hide scrollbar on highlight layer */
        div::-webkit-scrollbar {
          display: none;
        }

        /* Textarea scrollbar styles */
        textarea::-webkit-scrollbar {
          width: 12px;
          height: 12px;
        }

        textarea::-webkit-scrollbar-track {
          background: ${isDarkMode ? '#1e293b' : '#f3f4f6'};
        }

        textarea::-webkit-scrollbar-thumb {
          background: ${isDarkMode ? '#475569' : '#cbd5e1'};
          border-radius: 6px;
          border: 2px solid ${isDarkMode ? '#1e293b' : '#f3f4f6'};
        }

        textarea::-webkit-scrollbar-thumb:hover {
          background: #E67145;
        }

        textarea::-webkit-scrollbar-corner {
          background: ${isDarkMode ? '#1e293b' : '#f3f4f6'};
        }

        /* Selection color */
        textarea::selection {
          background-color: ${theme.selection};
        }
      `}</style>
    </div>
  );
}
