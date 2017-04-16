keyword 'var'
name 'add'
symbol '='
keyword 'func'
symbol '('
name 'x'
symbol ','
name 'y'
symbol ')'
indent
keyword 'return'
name 'x'
operator '+'
name 'y'
newline
dedent
newline
keyword 'var'
name 'mul'
symbol '='
keyword 'func'
symbol '('
name 'x'
symbol ','
name 'y'
symbol ')'
operator '->'
name 'x'
operator '*'
name 'y'
newline
keyword 'var'
name 'apply'
symbol '='
keyword 'func'
symbol '('
name 'fn'
symbol ','
name 'x'
symbol ','
name 'y'
symbol ')'
indent
keyword 'return'
name 'fn'
symbol '('
name 'x'
symbol ','
name 'y'
symbol ')'
newline
dedent
newline
keyword 'var'
name 'main'
symbol '='
keyword 'func'
symbol '('
symbol ')'
indent
name 'print'
symbol '('
name 'add'
symbol '('
int 3
symbol ','
int 4
symbol ')'
symbol ')'
newline
name 'print'
symbol '('
name 'mul'
symbol '('
int 3
symbol ','
int 4
symbol ')'
symbol ')'
newline
name 'print'
symbol '('
string '-----'
symbol ')'
newline
name 'print'
symbol '('
name 'apply'
symbol '('
name 'add'
symbol ','
int 3
symbol ','
int 4
symbol ')'
symbol ')'
newline
name 'print'
symbol '('
name 'apply'
symbol '('
name 'mul'
symbol ','
int 3
symbol ','
int 4
symbol ')'
symbol ')'
newline
name 'print'
symbol '('
name 'apply'
symbol '('
keyword 'func'
symbol '('
name 'x'
symbol ','
name 'y'
symbol ')'
operator '->'
int 2
operator '*'
name 'x'
operator '+'
name 'y'
symbol ','
int 3
symbol ','
int 4
symbol ')'
symbol ')'
newline
dedent
newline
EOF
