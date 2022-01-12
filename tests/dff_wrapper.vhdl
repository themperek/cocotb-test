-- This file is public domain, it can be freely copied without restrictions.
-- SPDX-License-Identifier: CC0-1.0

library ieee;
use ieee.std_logic_1164.all;

library some_lib;
use some_lib.dff_test_vhdl;

entity dff_wrapper is
port(
  clk: in std_logic;
  d: in std_logic;
  q: out std_logic);
end dff_wrapper;

architecture behavioral of dff_wrapper is
begin

  dff_inst: entity some_lib.dff_test_vhdl
  port map (
    clk => clk,
    d => d,
    q => q
  );

end behavioral;
