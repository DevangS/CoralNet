 /* ---------------------------------------------
  *  Y = INTSQRT(X) - A MEX-function using bitshifts
  *  to calculate to integer square root for any
  *  32-bit positive integer, i.e. the value y
  *  that fulfills y^2 <= x <= (y+1)^2. By using
  *  the remainder the output integer is rounded
  *  off towards the closest of the values y and
  *  y+1. Handles vector input, but not matrices.
  *
  *  2009-02-13, Henrik Blidh
    --------------------------------------------- */

/* Header files to be included */

#include "mex.h"

/* Input Arguments */

#define	X_IN	prhs[0]

/* Output Arguments */

#define	Y_OUT	plhs[0]

/* Macros */

#if !defined(MAX)
#define	MAX(A, B)	((A) > (B) ? (A) : (B))
#endif

#if !defined(MIN)
#define	MIN(A, B)	((A) < (B) ? (A) : (B))
#endif
 /* --------------------------------------------- */

static void intsqrt(double y[],
double	x[],
int      m)

{
    int k;
    unsigned Q = 0;
    unsigned D = 0;
    int R = 0;
    int i;
    for (k = 0; k<m; k++)
    {
        D = (unsigned) x[k];
        for (i = 15; i >= 0 ; i-- )
        {
            if (R>=0)
            {
                R = (R << 2) | ((D >> (i+i))&3);
                R = R - ((Q << 2)|1);
            } else {
                R = (R << 2) | ((D >> (i+i))&3);
                R = R + ((Q << 2)|3);
            }
            if (R >=0) {Q = (Q << 1)|1;}
            else {Q = (Q << 1)|0;}
        }
        if (R<0)
        {
            R = R+((Q<<1)|1);
        }
        if (R > (((Q+1)*(Q+1) - Q*Q)/2))
        {
            y[k] = Q+1;
        } else {
            y[k] = Q;
        }        
        Q = 0;
        R = 0;
    }
    return;
}

void mexFunction( int nlhs, mxArray *plhs[],
int nrhs, const mxArray *prhs[] )

{
    double *y;
    double *x;
    mwSize m,n;
    
    /* Check for proper number of arguments */
    
    if (nrhs != 1) {
        mexErrMsgTxt("One input argument only!");
    } else if (nlhs > 1) {
        mexErrMsgTxt("Too many output arguments.");
    }
    
    /* Check the dimensions of input X.*/
    
    m = mxGetM(X_IN);
    n = mxGetN(X_IN);
    if (!mxIsDouble(X_IN) || mxIsComplex(X_IN) || (MIN(m,n) != 1))
    {
        mexErrMsgTxt("INTSQRT(X) requires that X be a n x 1 vector.");
    }
    
    /* Create a matrix for the return argument */
    Y_OUT = mxCreateDoubleMatrix(m, n, mxREAL);
    
    /* Assign pointers to the various parameters */
    y = mxGetPr(Y_OUT);
    x = mxGetPr(X_IN);
    
    /* Do the actual computations in a subroutine */
    intsqrt(y,x,MAX(m,n));
    
    return;
}
