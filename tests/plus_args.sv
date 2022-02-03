
module plus_args (output reg user_mode);

    /* verilator lint_off WIDTH */

    initial begin
        user_mode = 0;
        if ($test$plusargs("USER_MODE")) begin 
            $display("plus_args:Configuring User mode");
            //Execute some code for this mode
            user_mode = 1;
        end
    end

    initial begin
        string testname = "";
        if ($value$plusargs("TEST=%s",testname)) begin
            $display("plus_args:Running TEST=%s.",testname);
        end
    end


endmodule
