keyword 'let'
name 'rect'
symbol '='
'table'
newline
name 'rect'
symbol '.'
name 'new'
symbol '='
keyword 'func'
symbol '('
name 'self'
symbol ')'
indent
keyword 'return'
'table'
keyword 'from'
name 'self'
newline
dedent
newline
name 'rect'
symbol '.'
name 'init'
symbol '='
keyword 'func'
symbol '('
name 'self'
symbol ','
name 'w'
symbol ','
name 'h'
symbol ')'
indent
name 'self'
symbol '.'
name 'w'
symbol '='
name 'w'
newline
name 'self'
symbol '.'
name 'h'
symbol '='
name 'h'
newline
dedent
newline
name 'rect'
symbol '.'
name 'area'
symbol '='
keyword 'func'
symbol '('
name 'self'
symbol ')'
indent
keyword 'return'
name 'self'
symbol '.'
name 'w'
operator '*'
name 'self'
symbol '.'
name 'h'
newline
dedent
newline
keyword 'let'
name 'square'
symbol '='
'table'
keyword 'from'
name 'rect'
newline
name 'square'
symbol '.'
name 'init'
symbol '='
keyword 'func'
symbol '('
name 'self'
symbol ','
name 's'
symbol ')'
indent
name 'self'
symbol '.'
name 'w'
symbol '='
name 's'
newline
name 'self'
symbol '.'
name 'h'
symbol '='
name 's'
newline
dedent
newline
keyword 'let'
name 'main'
symbol '='
keyword 'func'
symbol '('
symbol ')'
indent
keyword 'let'
name 'a'
symbol '='
name 'rect'
symbol ':'
name 'new'
symbol '('
symbol ')'
newline
name 'a'
symbol ':'
name 'init'
symbol '('
int 3
symbol ','
int 4
symbol ')'
newline
name 'print'
symbol '('
name 'a'
symbol ':'
name 'area'
symbol '('
symbol ')'
symbol ')'
newline
keyword 'let'
name 'b'
symbol '='
name 'square'
symbol ':'
name 'new'
symbol '('
symbol ')'
newline
name 'b'
symbol ':'
name 'init'
symbol '('
int 4
symbol ')'
newline
name 'print'
symbol '('
name 'b'
symbol ':'
name 'area'
symbol '('
symbol ')'
symbol ')'
newline
dedent
newline
EOF
