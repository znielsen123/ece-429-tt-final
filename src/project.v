/*
 * Copyright (c) 2026 Zach Nielsen
 * SPDX-License-Identifier: Apache-2.0
 *
 * 30-second basketball shot clock for Tiny Tapeout (sky130).
 * - Counts down from 30 to 0 at 1 Hz (derived from the 50 MHz TT clock).
 * - ui_in[0] reloads the count to 30 on a synchronous press.
 * - ui_in[1] pauses the countdown while held high.
 * - ui_in[2] selects display format: 0 = 5-bit binary on uo_out[4:0],
 *                                    1 = dual 7-segment on uo_out[6:0] + uio_out[6:0].
 * - uo_out[7] is the buzzer: high when the count is 0.
 */

`default_nettype none

module tt_um_znielsen123 #(
    parameter TICK_DIV = 50_000_000   // 50 MHz / 50M = 1 Hz tick
) (
    input  wire [7:0] ui_in,
    output wire [7:0] uo_out,
    input  wire [7:0] uio_in,
    output wire [7:0] uio_out,
    output wire [7:0] uio_oe,
    input  wire       ena,
    input  wire       clk,
    input  wire       rst_n
);

    localparam DIV_W = $clog2(TICK_DIV);

    wire reset_btn = ui_in[0];
    wire pause_btn = ui_in[1];
    wire mode_sel  = ui_in[2];

    // Clock divider: emit a single-cycle `tick` once every TICK_DIV clocks.
    reg [DIV_W-1:0] div_count;
    reg             tick;

    always @(posedge clk) begin
        if (!rst_n) begin
            div_count <= 0;
            tick      <= 1'b0;
        end else if (div_count == TICK_DIV - 1) begin
            div_count <= 0;
            tick      <= 1'b1;
        end else begin
            div_count <= div_count + 1'b1;
            tick      <= 1'b0;
        end
    end

    // Shot clock: 5-bit down counter, holds at 0.
    reg [4:0] shot_clock;

    always @(posedge clk) begin
        if (!rst_n)
            shot_clock <= 5'd30;
        else if (reset_btn)
            shot_clock <= 5'd30;
        else if (tick && !pause_btn && shot_clock != 5'd0)
            shot_clock <= shot_clock - 1'b1;
    end

    wire buzzer = (shot_clock == 5'd0);

    // BCD split for the 7-segment displays.
    reg [3:0] tens_digit, ones_digit;
    always @(*) begin
        if (shot_clock >= 5'd30) begin
            tens_digit = 4'd3;
            ones_digit = 4'd0;
        end else if (shot_clock >= 5'd20) begin
            tens_digit = 4'd2;
            ones_digit = shot_clock - 5'd20;
        end else if (shot_clock >= 5'd10) begin
            tens_digit = 4'd1;
            ones_digit = shot_clock - 5'd10;
        end else begin
            tens_digit = 4'd0;
            ones_digit = shot_clock[3:0];
        end
    end

    // Common-cathode 7-segment encoding: bits [6:0] = {g,f,e,d,c,b,a}, segment on = 1.
    function [6:0] seg7;
        input [3:0] d;
        begin
            case (d)
                4'h0:    seg7 = 7'b0111111;
                4'h1:    seg7 = 7'b0000110;
                4'h2:    seg7 = 7'b1011011;
                4'h3:    seg7 = 7'b1001111;
                4'h4:    seg7 = 7'b1100110;
                4'h5:    seg7 = 7'b1101101;
                4'h6:    seg7 = 7'b1111101;
                4'h7:    seg7 = 7'b0000111;
                4'h8:    seg7 = 7'b1111111;
                4'h9:    seg7 = 7'b1101111;
                default: seg7 = 7'b0000000;
            endcase
        end
    endfunction

    wire [6:0] ones_seg = seg7(ones_digit);
    wire [6:0] tens_seg = seg7(tens_digit);

    // Output muxing based on display mode.
    // Mode 0 (binary): uo_out[4:0] = shot_clock,  uio_out = 0
    // Mode 1 (7-seg):  uo_out[6:0] = ones_seg,    uio_out[6:0] = tens_seg
    // Buzzer (uo_out[7]) is the same in both modes.
    assign uo_out[6:0]   = mode_sel ? ones_seg : {2'b00, shot_clock};
    assign uo_out[7]     = buzzer;
    assign uio_out[6:0]  = mode_sel ? tens_seg : 7'b0000000;
    assign uio_out[7]    = 1'b0;
    assign uio_oe        = 8'b11111111;  // all uio pins are outputs

    // Silence unused-input warnings.
    wire _unused = &{ena, ui_in[7:3], uio_in, 1'b0};

endmodule
