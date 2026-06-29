%% schemaforge-report.cls
%% Datasheet-style design-report class for schema-forge /polish.
%% Build with lualatex (twice). Reproduces the canonical schema-forge
%% "Design & Build Guide" look: dark navy title page, accent callout
%% boxes, zebra spec/BOM tables, running header/footer with a green
%% verified-status stamp, and a landscape auto-rendered schematic page.
\NeedsTeXFormat{LaTeX2e}
\ProvidesClass{schemaforge-report}[2026/06/29 schema-forge design report]

\LoadClass[11pt]{article}

%% ---------------------------------------------------------------- fonts
%% Latin Modern (roman body, sans headings, CM-compatible math) — the
%% portable match for the reference guide rendered under LuaTeX.
\RequirePackage{lmodern}
\RequirePackage[T1]{fontenc}
\RequirePackage{textcomp}
\RequirePackage{microtype}

%% ------------------------------------------------------------- geometry
\RequirePackage[a4paper,top=2.4cm,bottom=2.2cm,left=2.3cm,right=2.3cm,
                headheight=14pt,headsep=18pt,footskip=26pt]{geometry}

%% --------------------------------------------------------------- colours
\RequirePackage{etoolbox}  % \ifstrequal
\RequirePackage{xcolor}
\definecolor{sfNavy}{HTML}{17314F}      % section heads, table headers, body title
\definecolor{sfTitleBg}{HTML}{0E2236}   % title-page background
\definecolor{sfGrid}{HTML}{1B3B5C}      % faint title-page grid
\definecolor{sfBlue}{HTML}{2E6DA4}      % accent / blue callout bar / topics
\definecolor{sfBlueBright}{HTML}{5A86C6}% title-page eyebrow + topics line
\definecolor{sfGreen}{HTML}{2E7D54}     % footer status + honesty callout bar
\definecolor{sfOlive}{HTML}{8A7A2E}     % load-bearing callout bar
\definecolor{sfBlueTint}{HTML}{EEF3FB}  % blue callout body
\definecolor{sfGreenTint}{HTML}{ECF4EF} % green callout body
\definecolor{sfOliveTint}{HTML}{F5F1E2} % olive callout body
\definecolor{sfZebra}{HTML}{EEF2F8}     % table zebra row
\definecolor{sfRule}{HTML}{9FB2C7}      % header/footer rules
\definecolor{sfMeta}{HTML}{B9C6D6}      % title-page metadata label

%% -------------------------------------------------------------- packages
\RequirePackage{graphicx}
\RequirePackage{booktabs}
\RequirePackage{colortbl}
\RequirePackage{array}
\RequirePackage{ragged2e}
\RequirePackage{pdflscape}
\RequirePackage{tikz}
\usetikzlibrary{calc}
\RequirePackage[most]{tcolorbox}
\RequirePackage{enumitem}
\setlist{leftmargin=1.4em,topsep=3pt,itemsep=3pt,parsep=0pt}
\RequirePackage[font=small,labelfont=bf,labelsep=period,
                justification=centering]{caption}

%% --------------------------------------------------------------- spacing
\setlength{\parindent}{0pt}
\setlength{\parskip}{6pt}
\renewcommand{\arraystretch}{1.25}

%% ----------------------------------------------------- section headings
\RequirePackage{titlesec}
\titleformat{\section}
  {\sffamily\Large\bfseries\color{sfNavy}}{\thesection}{0.8em}{}
  [\vspace{2pt}{\color{sfRule}\titlerule[1pt]}]
\titleformat{\subsection}
  {\sffamily\large\bfseries\color{sfNavy}}{\thesubsection}{0.6em}{}
\titlespacing*{\section}{0pt}{18pt}{8pt}
\titlespacing*{\subsection}{0pt}{12pt}{4pt}

%% ---------------------------------------------------- header and footer
\RequirePackage{fancyhdr}
\RequirePackage{lastpage}
%% \sfdoctitle — short circuit name (header left); \sfguidekind — header
%% right; \sffootleft — footer tagline; \sffootstatus — green stamp.
\newcommand{\sfdoctitle}{Design Report}
\newcommand{\sfguidekind}{Design \& Build Guide}
\newcommand{\sffootleft}{schema-forge}
\newcommand{\sffootstatus}{verified $\cdot$ SPICE}
\newcommand{\setdoctitle}[1]{\renewcommand{\sfdoctitle}{#1}}
\newcommand{\setguidekind}[1]{\renewcommand{\sfguidekind}{#1}}
\newcommand{\setfootleft}[1]{\renewcommand{\sffootleft}{#1}}
\newcommand{\setfootstatus}[1]{\renewcommand{\sffootstatus}{#1}}

\fancypagestyle{sfmain}{%
  \fancyhf{}%
  \renewcommand{\headrulewidth}{0.8pt}%
  \renewcommand{\footrulewidth}{0.8pt}%
  \renewcommand{\headrule}{\hbox to\headwidth{\color{sfRule}\leaders\hrule height \headrulewidth\hfill}}%
  \renewcommand{\footrule}{\hbox to\headwidth{\color{sfRule}\leaders\hrule height \footrulewidth\hfill}}%
  \fancyhead[L]{\sffamily\bfseries\color{sfNavy}\small\sfdoctitle}%
  \fancyhead[R]{\sffamily\color{sfNavy}\small\sfguidekind}%
  \fancyfoot[L]{\sffamily\footnotesize\color{sfNavy}\sffootleft}%
  \fancyfoot[C]{\sffamily\footnotesize\color{sfNavy}\thepage}%
  \fancyfoot[R]{\sffamily\footnotesize\bfseries\color{sfGreen}\sffootstatus}%
}
\pagestyle{sfmain}

%% ------------------------------------------------------------- callouts
%% \begin{callout}{<blue|green|olive>}{Header text} ... \end{callout}
\newcommand{\sf@calloutbar}{sfBlue}
\newcommand{\sf@calloutbg}{sfBlueTint}
\NewDocumentEnvironment{callout}{m m +b}{%
  \renewcommand{\sf@calloutbar}{sfBlue}\renewcommand{\sf@calloutbg}{sfBlueTint}%
  \ifstrequal{#1}{green}{\renewcommand{\sf@calloutbar}{sfGreen}\renewcommand{\sf@calloutbg}{sfGreenTint}}{}%
  \ifstrequal{#1}{olive}{\renewcommand{\sf@calloutbar}{sfOlive}\renewcommand{\sf@calloutbg}{sfOliveTint}}{}%
  \begin{tcolorbox}[enhanced,sharp corners,boxrule=0pt,
    colback=\sf@calloutbg,
    borderline west={2.5pt}{0pt}{\sf@calloutbar},
    left=10pt,right=10pt,top=8pt,bottom=8pt,
    before skip=10pt,after skip=10pt,
    title={#2},coltitle=white,colbacktitle=\sf@calloutbar,
    fonttitle=\sffamily\bfseries\small,
    attach boxed title to top left={xshift=0pt,yshift=0pt},
    boxed title style={sharp corners,boxrule=0pt,top=3pt,bottom=3pt,left=10pt,right=10pt},
    enlarge top by=0pt]%
  #3
  \end{tcolorbox}%
}{}

%% --------------------------------------------------------------- tables
%% Navy header row + white text; zebra body. Wrap a tabular in
%% \rowcolors{2}{white}{sfZebra} and use \sfhead for the header row.
\newcommand{\sfhead}[1]{\rowcolor{sfNavy}\color{white}\sffamily\bfseries #1}
\newcommand{\sfheadcell}[1]{\textcolor{white}{\sffamily\bfseries #1}}
% group-divider row inside BOM-style tables
\newcommand{\sfgrouprow}[2]{\rowcolor{sfBlue}\multicolumn{#1}{l}{\textcolor{white}{\sffamily\bfseries #2}}}

%% --------------------------------------------------------- title page
%% Setters for the cover. \sfmaketitle draws it.
\newcommand{\sf@eyebrow}{SCHEMA-FORGE $\cdot$ VERIFIED BY SIMULATION}
\newcommand{\sf@title}{Design Report}
\newcommand{\sf@subtitle}{}
\newcommand{\sf@topics}{}
\newcommand{\sf@statusbanner}{}
\newcommand{\sf@metatable}{}
\newcommand{\setcovereyebrow}[1]{\renewcommand{\sf@eyebrow}{#1}}
\newcommand{\setcovertitle}[1]{\renewcommand{\sf@title}{#1}}
\newcommand{\setcoversubtitle}[1]{\renewcommand{\sf@subtitle}{#1}}
\newcommand{\setcovertopics}[1]{\renewcommand{\sf@topics}{#1}}
\newcommand{\setcoverstatus}[1]{\renewcommand{\sf@statusbanner}{#1}}
% rows of "Label & Value\\" for the cover footer metadata block
\newcommand{\setcovermeta}[1]{\renewcommand{\sf@metatable}{#1}}

\newcommand{\sfmaketitle}{%
\begin{titlepage}%
\thispagestyle{empty}%
\begin{tikzpicture}[remember picture,overlay]
  \fill[sfTitleBg] (current page.south west) rectangle (current page.north east);
  % faint grid over the upper band
  \begin{scope}
    \clip (current page.north west) rectangle ($(current page.north east)+(0,-9.2cm)$);
    \draw[sfGrid,line width=0.3pt,opacity=0.6,step=0.62cm]
      ($(current page.north west)+(0,0)$) grid ($(current page.north east)+(0,-10cm)$);
  \end{scope}
  \begin{scope}[shift={(current page.north west)}]
    \node[anchor=north west,text width=\paperwidth-5cm,inner sep=0pt]
      at (2.5cm,-2.6cm) {%
      {\sffamily\bfseries\color{sfBlueBright}\large \sf@eyebrow}\\[1.2cm]
      {\sffamily\bfseries\color{white}\fontsize{34}{40}\selectfont \sf@title}\\[1.0cm]
      {\sffamily\color{sfMeta}\large \sf@subtitle}\\[0.7cm]
      {\sffamily\color{sfBlueBright} \sf@topics}\\[0.6cm]
      {\sffamily\bfseries\color{white} \sf@statusbanner}%
    };
  \end{scope}
  % metadata block low on the page
  \begin{scope}[shift={(current page.south west)}]
    \node[anchor=south west,inner sep=0pt] at (2.5cm,3.2cm) {%
      \color{white}\sffamily\footnotesize
      \renewcommand{\arraystretch}{1.25}%
      \begin{tabular}{@{}p{2.4cm}@{}p{11cm}@{}}\sf@metatable\end{tabular}};
  \end{scope}
\end{tikzpicture}%
\end{titlepage}%
}

%% Cover metadata label helper (dim label, white value).
\newcommand{\metalabel}[1]{\textcolor{sfMeta}{#1}}

%% ----------------------------------------------- landscape schematic page
%% \schematicpage{<image file>}{<caption>} — a full rotated page holding the
%% auto-rendered schematic, vertically centred and bounded so it NEVER spills
%% past the running header/footer rules. Use instead of a hand-rolled
%% landscape+figure (which floats and can overflow into the header).
\RequirePackage{graphbox}  % vertical-align includegraphics; safe if unused
\newcommand{\schematicpage}[2]{%
  \clearpage
  \begin{landscape}%
  \thispagestyle{sfmain}%
  \vspace*{\fill}%
  \begin{center}%
    % Fill the wide landscape page: in a landscape env \textwidth stays at the
    % portrait width, so widen to use the long edge. keepaspectratio + the
    % height cap means a *tall* schematic shrinks to fit instead of overflowing,
    % and the height cap leaves room for the caption above the footer rule.
    \makebox[\linewidth][c]{%
      \includegraphics[width=1.35\textwidth,height=0.82\textheight,keepaspectratio]{#1}}\\[10pt]
    \captionof{figure}{#2}%
  \end{center}%
  \vspace*{\fill}%
  \end{landscape}%
}

\endinput
