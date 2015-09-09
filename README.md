This repository contains a Python script that does simple static analysis of P4 programs to determine if programmers are inadvertently using sequential semantics instead of parallel semantics.

It also contains the results of the this analysis on switch.p4 as a slide deck: p4-semantics.pdf

To use the static checker:

1. Follow instructions here to install the p4-hlir Python module: https://github.com/p4lang/p4-hlir

2. Then move into the top level of the P4 program you want to analyze and run: python p4-semantics.py program_name.

3. For example, to analyze switch.p4 (https://github.com/p4lang/p4factory/blob/master/targets/switch/p4src/switch.p4),
   clone https://github.com/p4lang/p4factory and change directories to the p4src directory.
