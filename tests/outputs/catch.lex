keyword 'var'
name 'three'
symbol '='
keyword 'func'
symbol '('
symbol ')'
indent
name 'panic'
symbol '('
string 'three!'
symbol ')'
newline
dedent
newline
keyword 'var'
name 'two'
symbol '='
keyword 'func'
symbol '('
symbol ')'
indent
keyword 'var'
name 'x'
symbol '='
name 'three'
symbol '?'
symbol '('
symbol ')'
newline
name 'print'
symbol '('
string 'two caught '
operator '$'
name 'tostr'
symbol '('
name 'x'
symbol ')'
symbol ')'
newline
dedent
newline
keyword 'var'
name 'one'
symbol '='
keyword 'func'
symbol '('
symbol ')'
indent
keyword 'var'
name 'x'
symbol '='
keyword 'catch'
indent
name 'two'
symbol '('
symbol ')'
newline
dedent
newline
name 'print'
symbol '('
string 'one caught '
operator '$'
name 'tostr'
symbol '('
name 'x'
symbol ')'
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
string '----'
symbol ')'
newline
keyword 'var'
name 'x'
symbol '='
keyword 'catch'
indent
name 'print'
symbol '('
string 'before'
symbol ')'
newline
name 'one'
symbol '('
symbol ')'
newline
name 'print'
symbol '('
string 'after'
symbol ')'
newline
dedent
newline
name 'print'
symbol '('
string 'main caught '
operator '$'
name 'tostr'
symbol '('
name 'x'
symbol ')'
symbol ')'
newline
name 'print'
symbol '('
string '----'
symbol ')'
newline
name 'print'
symbol '('
string 'before'
symbol ')'
newline
name 'x'
symbol '='
name 'one'
symbol '?'
symbol '('
symbol ')'
newline
name 'print'
symbol '('
string 'after'
symbol ')'
newline
name 'print'
symbol '('
string 'main caught '
operator '$'
name 'tostr'
symbol '('
name 'x'
symbol ')'
symbol ')'
newline
name 'print'
symbol '('
string '----'
symbol ')'
newline
name 'x'
symbol '='
keyword 'catch'
indent
name 'print'
symbol '('
string 'before'
symbol ')'
newline
name 'panic'
symbol '('
string 'obvious'
symbol ')'
newline
name 'print'
symbol '('
string 'after'
symbol ')'
newline
dedent
newline
name 'print'
symbol '('
string 'main caught '
operator '$'
name 'tostr'
symbol '('
name 'x'
symbol ')'
symbol ')'
newline
name 'print'
symbol '('
string '----'
symbol ')'
newline
name 'print'
symbol '('
string 'before'
symbol ')'
newline
name 'x'
symbol '='
name 'panic'
symbol '?'
symbol '('
string 'obvious'
symbol ')'
newline
name 'print'
symbol '('
string 'after'
symbol ')'
newline
name 'print'
symbol '('
string 'main caught '
operator '$'
name 'tostr'
symbol '('
name 'x'
symbol ')'
symbol ')'
newline
dedent
newline
EOF
