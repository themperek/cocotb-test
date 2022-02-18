`timescale 1ns/1ns

module glbl ();

    reg rst;

    initial begin
        rst = 1;
        #10
        rst = 0;
    end
endmodule
