`timescale 1ns/1ps

module test;
   reg CLK, A;     // create signals for inputs of unit under test
   ex uut(CLK, A); // create instance named "uut" of module "ex"

   initial begin
      {uut.s1,uut.s0} <= 0;       // initialize state bits
      CLK             <= 0;       // clock (1st input) starts low
      A               <= $random; // 2nd input gets random init value 
      // $dumpfile("test.vcd"); // if desired, for waveform viewing
      #20 $finish; // wait 20ns, then end simulation
   end
   
   always #0.5 CLK=~CLK; // clock toggles every 0.5 ns
   
   // do this at end of each cycle
   always @(posedge CLK) begin
      
      // values printed by $display are right before FFs update
      $display("%6t  ",$realtime,
	       " state: ", uut.s1, uut.s0,
	       " input: ", uut.a,
	       " -> nextstate: ", uut.ns1, uut.ns0 );

      // check if target state is reached
      if ({uut.s1,uut.s0} == 2'b10) begin
	 $display("[current state is target state]\n");
	 //$finish; 
      end
      
      // set input for next cycle. change is synchronous to FFs in uut
      A <= $random;

   end
endmodule // end of testbench module

module ex(clock,a);
   input clock,a;
   reg 	 s0,s1;
   wire  b,ns0,ns1;
   and g0(b,a,s0);
   not g1(ns0,b);
   not g2(ns1,s1);
   always @(posedge clock) begin
      s0<=ns0;
      s1<=ns1;
   end
endmodule

