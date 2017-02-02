keyword 'import'
name 'array'
newline
keyword 'let'
name 'gadd'
symbol '='
keyword 'func'
symbol '('
name 'a'
symbol ','
name 'b'
symbol ')'
operator '->'
name 'a'
operator '+'
name 'b'
newline
keyword 'let'
name 'main'
symbol '='
keyword 'func'
symbol '('
symbol ')'
indent
keyword 'let'
name 'ladd'
symbol '='
keyword 'func'
symbol '('
name 'a'
symbol ','
name 'b'
symbol ')'
operator '->'
name 'a'
operator '+'
name 'b'
newline
keyword 'let'
name 'a'
symbol '='
'table'
newline
name 'a'
symbol '['
int 0
symbol ']'
symbol '='
int 1
newline
name 'a'
symbol '['
int 1
symbol ']'
symbol '='
int 2
newline
name 'a'
symbol '['
int 2
symbol ']'
symbol '='
int 3
newline
name 'print'
symbol '('
name 'array'
symbol '.'
name 'foldl'
symbol '('
name 'a'
symbol ','
name 'gadd'
symbol ','
int 0
symbol ')'
symbol ')'
newline
name 'print'
symbol '('
name 'array'
symbol '.'
name 'foldl'
symbol '('
name 'a'
symbol ','
name 'ladd'
symbol ','
int 0
symbol ')'
symbol ')'
newline
dedent
newline
EOF
