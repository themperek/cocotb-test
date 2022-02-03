
`include "inc.sv"

module test_parameters #(
    parameter WIDTH_IN = 8,
    parameter WIDTH_OUT = 8
) (
    input  [WIDTH_IN-1:0]   data_in,
    output [WIDTH_OUT-1:0]  data_out,
    output [`DEFINE-1:0] define_out
);

endmodule
