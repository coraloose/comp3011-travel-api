// Kernel for matrix transposition.
// One work-item handles one input matrix element.

__kernel void transposeMatrix(__global const float *input,
                              __global float *output,
                              const int nRows,
                              const int nCols)
{
    int col = get_global_id(0);
    int row = get_global_id(1);

    int inputIndex  = row * nCols + col;
    int outputIndex = col * nRows + row;

    output[outputIndex] = input[inputIndex];
}
