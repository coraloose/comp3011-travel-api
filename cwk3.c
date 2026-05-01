//
// OpenCL coursework for COMP3221 Parallel Computation.
//
// Generative AI declaration:
// I used ChatGPT to help draft and check this OpenCL matrix transpose implementation.
// The code was reviewed and adapted by me.
//

#include <stdio.h>
#include <stdlib.h>

#include "helper_cwk.h"

#define CHECK_CL(status, message)                         \
    do {                                                  \
        if ((status) != CL_SUCCESS) {                     \
            printf("%s failed with error %d.\n",         \
                   (message), (int)(status));             \
            exit(EXIT_FAILURE);                           \
        }                                                 \
    } while (0)

int main( int argc, char **argv )
{
    int nRows, nCols;
    getCmdLineArgs( argc, argv, &nRows, &nCols );

    cl_device_id device;
    cl_context context = simpleOpenContext_GPU(&device);

    cl_int status;
    cl_command_queue queue = clCreateCommandQueue( context, device, 0, &status );
    CHECK_CL(status, "clCreateCommandQueue");

    size_t nItems = (size_t)nRows * (size_t)nCols;
    size_t nBytes = nItems * sizeof(float);

    float *hostMatrix = (float*) malloc( nBytes );
    if( hostMatrix == NULL )
    {
        printf( "Failed to allocate host matrix.\n" );
        exit( EXIT_FAILURE );
    }

    fillMatrix( hostMatrix, nRows, nCols );
    printf( "Original matrix (only top-left shown if too large):\n" );
    displayMatrix( hostMatrix, nRows, nCols );

    // Compile the kernel.
    cl_kernel kernel = compileKernelFromFile( "cwk3.cl", "transposeMatrix", context, device );

    // Allocate device memory.
    cl_mem deviceInput = clCreateBuffer( context, CL_MEM_READ_ONLY, nBytes, NULL, &status );
    CHECK_CL(status, "clCreateBuffer input");

    cl_mem deviceOutput = clCreateBuffer( context, CL_MEM_WRITE_ONLY, nBytes, NULL, &status );
    CHECK_CL(status, "clCreateBuffer output");

    // Copy the input matrix to the GPU.
    status = clEnqueueWriteBuffer( queue, deviceInput, CL_TRUE, 0, nBytes, hostMatrix, 0, NULL, NULL );
    CHECK_CL(status, "clEnqueueWriteBuffer");

    // Set kernel arguments.
    status  = clSetKernelArg( kernel, 0, sizeof(cl_mem), &deviceInput );
    status |= clSetKernelArg( kernel, 1, sizeof(cl_mem), &deviceOutput );
    status |= clSetKernelArg( kernel, 2, sizeof(int), &nRows );
    status |= clSetKernelArg( kernel, 3, sizeof(int), &nCols );
    CHECK_CL(status, "clSetKernelArg");

    // One work-item transposes one matrix element.
    size_t globalSize[2] = { (size_t)nCols, (size_t)nRows };
    status = clEnqueueNDRangeKernel( queue, kernel, 2, NULL, globalSize, NULL, 0, NULL, NULL );
    CHECK_CL(status, "clEnqueueNDRangeKernel");

    status = clFinish( queue );
    CHECK_CL(status, "clFinish");

    // Copy the transposed matrix back into hostMatrix.
    status = clEnqueueReadBuffer( queue, deviceOutput, CL_TRUE, 0, nBytes, hostMatrix, 0, NULL, NULL );
    CHECK_CL(status, "clEnqueueReadBuffer");

    printf( "Transposed matrix (only top-left shown if too large):\n" );
    displayMatrix( hostMatrix, nCols, nRows );

    clReleaseMemObject    ( deviceInput  );
    clReleaseMemObject    ( deviceOutput );
    clReleaseKernel       ( kernel       );
    clReleaseCommandQueue ( queue        );
    clReleaseContext      ( context      );

    free( hostMatrix );

    return EXIT_SUCCESS;
}
