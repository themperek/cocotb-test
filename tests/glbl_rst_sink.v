`timescale 1ns/1ns

module glbl_rst_sink ();

    wire rst;

    assign rst = glbl_rst.rst;

endmodule