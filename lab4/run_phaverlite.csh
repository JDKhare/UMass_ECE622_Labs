#!/bin/tcsh -f
# Run PHAVerLite on nmos_model.pha from lab4 (no need to pre-source env).
# Usage from lab4:  tcsh run_phaverlite.csh
# Or:             chmod +x run_phaverlite.csh && ./run_phaverlite.csh

set lab4 = `dirname $0`
set lab4 = `cd $lab4 && pwd`
cd $lab4/../setups
source ./env.csh
if ($status != 0) exit 1
cd $lab4
exec phaverlite $lab4/nmos_model.pha
