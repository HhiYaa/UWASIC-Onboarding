`default_nettype none

module spi_peripheral (
    input  wire clk,
    input  wire rst_n,

    // SPI signals
    input  wire COPI,
    input  wire nCS,
    input  wire SCLK,

    // Register outputs to PWM module
    output reg [7:0] en_reg_out_7_0,
    output reg [7:0] en_reg_out_15_8,
    output reg [7:0] en_reg_pwm_7_0,
    output reg [7:0] en_reg_pwm_15_8,
    output reg [7:0] pwm_duty_cycle
);


// CDC Synchronizers
    reg SCLK_sync1, SCLK_sync2, SCLK_prev;
    reg nCS_sync1,  nCS_sync2;
    reg COPI_sync1, COPI_sync2;

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            SCLK_sync1 <= 1'b0;
            SCLK_sync2 <= 1'b0;
            SCLK_prev  <= 1'b0;
            nCS_sync1  <= 1'b1;
            nCS_sync2  <= 1'b1;
            COPI_sync1 <= 1'b0;
            COPI_sync2 <= 1'b0;
        end else begin
            SCLK_sync1 <= SCLK;
            SCLK_sync2 <= SCLK_sync1;
            SCLK_prev  <= SCLK_sync2;
            nCS_sync1  <= nCS;
            nCS_sync2  <= nCS_sync1;
            COPI_sync1 <= COPI;
            COPI_sync2 <= COPI_sync1;
        end
    end


// Edge Detection
    wire SCLK_rising = (SCLK_sync2 == 1'b1) && (SCLK_prev  == 1'b0);
    wire nCS_posedge = (nCS_sync1  == 1'b1) && (nCS_sync2  == 1'b0);


// Shift Register
    reg [15:0] shift_reg;
    reg [4:0]  bit_count;

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            shift_reg <= 16'b0;
            bit_count <= 5'b0;
        end else if (nCS_sync2 == 1'b0) begin
            // transaction in progress - collect bits
            if (SCLK_rising) begin
                shift_reg <= {shift_reg[14:0], COPI_sync2};
                bit_count <= bit_count + 1;
            end
        end else begin
            // transaction ended - reset counter for next time
            bit_count <= 5'b0;
        end
    end


// Register Decoding
    localparam MAX_ADDR = 7'h04;

    wire       rw_bit  = shift_reg[15];      // 1=write, 0=read
    wire [6:0] address = shift_reg[14:8];    // which register
    wire [7:0] data    = shift_reg[7:0];     // what value

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            en_reg_out_7_0  <= 8'h00;
            en_reg_out_15_8 <= 8'h00;
            en_reg_pwm_7_0  <= 8'h00;
            en_reg_pwm_15_8 <= 8'h00;
            pwm_duty_cycle  <= 8'h00;
        end else if (nCS_posedge && rw_bit && (address <= MAX_ADDR) && (bit_count == 16)) begin
            case (address)
                7'h00: en_reg_out_7_0  <= data;
                7'h01: en_reg_out_15_8 <= data;
                7'h02: en_reg_pwm_7_0  <= data;
                7'h03: en_reg_pwm_15_8 <= data;
                7'h04: pwm_duty_cycle  <= data;
                default: ;
            endcase
        end
    end

endmodule