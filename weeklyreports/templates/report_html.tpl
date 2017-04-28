<!DOCTYPE html>
<html>
<head>
    <title>Flask Template Example</title>
    <style>
        .highlight .hll { background-color: #49483e }
        .highlight  { background: #272822; color: #f8f8f2 }
        .highlight .c { color: #75715e } /* Comment */
        .highlight .err { color: #960050; background-color: #1e0010 } /* Error */
        .highlight .k { color: #66d9ef } /* Keyword */
        .highlight .l { color: #ae81ff } /* Literal */
        .highlight .n { color: #f8f8f2 } /* Name */
        .highlight .o { color: #f92672 } /* Operator */
        .highlight .p { color: #f8f8f2 } /* Punctuation */
        .highlight .ch { color: #75715e } /* Comment.Hashbang */
        .highlight .cm { color: #75715e } /* Comment.Multiline */
        .highlight .cp { color: #75715e } /* Comment.Preproc */
        .highlight .cpf { color: #75715e } /* Comment.PreprocFile */
        .highlight .c1 { color: #75715e } /* Comment.Single */
        .highlight .cs { color: #75715e } /* Comment.Special */
        .highlight .gd { color: #f92672 } /* Generic.Deleted */
        .highlight .ge { font-style: italic } /* Generic.Emph */
        .highlight .gi { color: #a6e22e } /* Generic.Inserted */
        .highlight .gs { font-weight: bold } /* Generic.Strong */
        .highlight .gu { color: #75715e } /* Generic.Subheading */
        .highlight .kc { color: #66d9ef } /* Keyword.Constant */
        .highlight .kd { color: #66d9ef } /* Keyword.Declaration */
        .highlight .kn { color: #f92672 } /* Keyword.Namespace */
        .highlight .kp { color: #66d9ef } /* Keyword.Pseudo */
        .highlight .kr { color: #66d9ef } /* Keyword.Reserved */
        .highlight .kt { color: #66d9ef } /* Keyword.Type */
        .highlight .ld { color: #e6db74 } /* Literal.Date */
        .highlight .m { color: #ae81ff } /* Literal.Number */
        .highlight .s { color: #e6db74 } /* Literal.String */
        .highlight .na { color: #a6e22e } /* Name.Attribute */
        .highlight .nb { color: #f8f8f2 } /* Name.Builtin */
        .highlight .nc { color: #a6e22e } /* Name.Class */
        .highlight .no { color: #66d9ef } /* Name.Constant */
        .highlight .nd { color: #a6e22e } /* Name.Decorator */
        .highlight .ni { color: #f8f8f2 } /* Name.Entity */
        .highlight .ne { color: #a6e22e } /* Name.Exception */
        .highlight .nf { color: #a6e22e } /* Name.Function */
        .highlight .nl { color: #f8f8f2 } /* Name.Label */
        .highlight .nn { color: #f8f8f2 } /* Name.Namespace */
        .highlight .nx { color: #a6e22e } /* Name.Other */
        .highlight .py { color: #f8f8f2 } /* Name.Property */
        .highlight .nt { color: #f92672 } /* Name.Tag */
        .highlight .nv { color: #f8f8f2 } /* Name.Variable */
        .highlight .ow { color: #f92672 } /* Operator.Word */
        .highlight .w { color: #f8f8f2 } /* Text.Whitespace */
        .highlight .mb { color: #ae81ff } /* Literal.Number.Bin */
        .highlight .mf { color: #ae81ff } /* Literal.Number.Float */
        .highlight .mh { color: #ae81ff } /* Literal.Number.Hex */
        .highlight .mi { color: #ae81ff } /* Literal.Number.Integer */
        .highlight .mo { color: #ae81ff } /* Literal.Number.Oct */
        .highlight .sa { color: #e6db74 } /* Literal.String.Affix */
        .highlight .sb { color: #e6db74 } /* Literal.String.Backtick */
        .highlight .sc { color: #e6db74 } /* Literal.String.Char */
        .highlight .dl { color: #e6db74 } /* Literal.String.Delimiter */
        .highlight .sd { color: #e6db74 } /* Literal.String.Doc */
        .highlight .s2 { color: #e6db74 } /* Literal.String.Double */
        .highlight .se { color: #ae81ff } /* Literal.String.Escape */
        .highlight .sh { color: #e6db74 } /* Literal.String.Heredoc */
        .highlight .si { color: #e6db74 } /* Literal.String.Interpol */
        .highlight .sx { color: #e6db74 } /* Literal.String.Other */
        .highlight .sr { color: #e6db74 } /* Literal.String.Regex */
        .highlight .s1 { color: #e6db74 } /* Literal.String.Single */
        .highlight .ss { color: #e6db74 } /* Literal.String.Symbol */
        .highlight .bp { color: #f8f8f2 } /* Name.Builtin.Pseudo */
        .highlight .fm { color: #a6e22e } /* Name.Function.Magic */
        .highlight .vc { color: #f8f8f2 } /* Name.Variable.Class */
        .highlight .vg { color: #f8f8f2 } /* Name.Variable.Global */
        .highlight .vi { color: #f8f8f2 } /* Name.Variable.Instance */
        .highlight .vm { color: #f8f8f2 } /* Name.Variable.Magic */
        .highlight .il { color: #ae81ff } /* Literal.Number.Integer.Long */
    </style>
</head>
<body>
{{ html }}
</body>
</html>