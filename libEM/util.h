/**
 * $Id$
 */
#ifndef eman__util_h__
#define eman__util_h__ 1

#include <stdio.h>
#include <string>
#include <vector>
#include <math.h>

#ifdef WIN32
#define M_PI 3.14159265358979323846f
#define MAXPATHLEN 1024
#endif

using std::string;
using std::vector;

namespace EMAN
{
	/** Util is a collection of utility functions.
     */
	class Util
	{
	  public:
		/** convert complex data array from Amplitude/Phase format
		 * into Real/Imaginary format.
		 * @param data complex data array.
		 * @param n array size.
		 */
		static void ap2ri(float *data, size_t n);

		/** flip the phase of a complex data array.
		 * @param data complex data array.
		 * @param n array size.
		 */
		static void flip_complex_phase(float *data, size_t n);
		static int file_lock_wait(FILE * file);
		static void file_unlock(FILE * file);

		/** check whether a file starts with certain magic string.
		 * @param first_block The first block of the file.
		 * @param magic The magic string to identify a file format.
		 * @return True if file matches magic. Otherwise, false.
		 */
		static bool check_file_by_magic(const void *first_block, const char *magic);

		/** check whether a file exists or not */
		static bool is_file_exist(string filename);

		
		/** Vertically flip the data of a 2D real image.
		 * @param data Data array of the 2D real image.
		 * @param nx Image Width.
		 * @param ny Image Height.
		 */
		static void flip_image(float *data, size_t nx, size_t ny);

		static bool sstrncmp(const char *s1, const char *s2);
		static string int2str(int n);
		static string get_line_from_string(char **str);
		
		static bool get_str_float(const char *s, const char *float_var, float *p_val);
		static bool get_str_float(const char *s, const char *float_var, float *p_v1, float *p_v2);
		static bool get_str_float(const char *s, const char *float_var, int *p_v0, float *p_v1,
								  float *p_v2);

		static bool get_str_int(const char *s, const char *int_var, int *p_val);
		static bool get_str_int(const char *s, const char *int_var, int *p_v1, int *p_v2);
		static bool get_str_int(const char *s, const char *int_var, int *p_v0, int *p_v1,
								int *p_v2);

		static string get_filename_by_ext(string old_filename, string ext);

		static string sbasename(const string & filename);
		
		static void calc_least_square_fit(size_t nitems, const float *data_x, const float *data_y,
										  float *slope, float *intercept, bool ignore_zero);

		static void save_data(const vector < float >&x_array, const vector < float >&y_array,
							  string filename);
		static void save_data(float x0, float dx, const vector < float >&y_array, string filename);
		static void save_data(float x0, float dx, float *y_array, size_t array_size,
							  string filename);

		static float get_frand(int low, int high);
		static float get_frand(float low, float high);
		static float get_frand(double low, double high);
		
		static float get_gauss_rand(float mean, float sigma);

		static inline int round(float x)
		{
			if (x < 0) {
				return (int) (x - 0.5f);
			}
			return (int) (x + 0.5f);
		}

	    static inline int round(double x)
		{
			if (x < 0) {
				return (int) (x - 0.5);
			}
			return (int) (x + 0.5);
		}
		// p1=x0,y0, p2=x1,y0; p3=x1,y1; p4=x0,y1 
		static inline float bilinear_interpolate(float p1, float p2, float p3, float p4, float t,
												 float u)
		{
			return (1 - t) * (1 - u) * p1 + t * (1 - u) * p2 + t * u * p3 + (1 - t) * u * p4;
		}

		// p1=x0,y0,z0; p2=x1,y0,z0; p3=x0,y1,z0, p4=x1,y1,z0
		// p5=x0,y0,z1; p6=x1,y0,z1; p7=x0,y1,z1, p8=x1,y1,z1
		static inline float trilinear_interpolate(float p1, float p2, float p3, float p4, float p5,
												  float p6, float p7, float p8, float t, float u,
												  float v)
		{
			return ((1 - t) * (1 - u) * (1 - v) * p1 + t * (1 - u) * (1 - v) * p2
					+ (1 - t) * u * (1 - v) * p3 + t * u * (1 - v) * p4
					+ (1 - t) * (1 - u) * v * p5 + t * (1 - u) * v * p6
					+ (1 - t) * u * v * p7 + t * u * v * p8);
		}


		static void find_max(float *data, size_t nitems, float *max_val, int *max_index = 0);
		static void find_min_and_max(float *data, size_t nitems, float *max_val, float *min_val,
									 int *max_i = 0, int *min_i = 0);
		static int calc_best_fft_size(int low);

		static int square(int n)
		{
			return n * n;
		}

		static float square(float x)
		{
			return x * x;
		}
		static float square(double x)
		{
			return (float)(x * x);
		}

		/** result = (x*x + y*y); */
		static float square_sum(float x, float y)
		{
			return (float)(x * x + y * y);
		}

		/** result = sqrt(x*x + y*y + z*z); */
		static inline float hypot3(int x, int y, int z)
		{
			return (float) sqrt((float)(x * x + y * y + z * z));
		}

		/** result = sqrt(x*x + y*y + z*z); */
		static inline float hypot3(float x, float y, float z)
		{
			return (float) sqrt(x * x + y * y + z * z);
		}
		/** result = sqrt(x*x + y*y + z*z); */
		static inline float hypot3(double x, double y, double z)
		{
			return (float) sqrt(x * x + y * y + z * z);
		}

		static inline int fast_floor(float x)
		{
			if (x < 0) {
				return ((int) x - 1);
			}
			return (int) x;
		}
		
		static inline float agauss(float a, float dx, float dy, float dz, float d)
		{
			return (a * exp(-(dx * dx + dy * dy + dz * dz) / d));
		}

		/** Get the minimum of 2 int numbers */
		static inline int min(int f1, int f2)
		{
			return (f1 < f2 ? f1 : f2);
		}
		/** Get the minimum of 3 int numbers */
		static inline int min(int f1, int f2, int f3)
		{
			if (f1 <= f2 && f1 <= f3) {
				return f1;
			}
			if (f2 <= f1 && f2 <= f3) {
				return f2;
			}
			return f3;
		}
		
		/** Get the minimum of 2 float numbers */
		static inline float min(float f1, float f2)
		{
			return (f1 < f2 ? f1 : f2);
		}
		/** Get the minimum of 3 float numbers */
		static inline float min(float f1, float f2, float f3)
		{
			if (f1 <= f2 && f1 <= f3) {
				return f1;
			}
			if (f2 <= f1 && f2 <= f3) {
				return f2;
			}
			return f3;
		}
		/** Get the minimum of 4 float numbers */
		static inline float min(float f1, float f2, float f3, float f4)
		{
			float m = f1;
			if (f2 < m) {
				m = f2;
			}
			if (f3 < m) {
				m = f3;
			}
			if (f4 < m) {
				m = f4;
			}
			return m;
		}
		
		/** Get the maximum of 2 float numbers */
		static inline float max(float f1, float f2)
		{
			return (f1 < f2 ? f2 : f1);
		}
		
		/** Get the maximum of 3 float numbers */
		static inline float max(float f1, float f2, float f3)
		{
			if (f1 >= f2 && f1 >= f3) {
				return f1;
			}
			if (f2 >= f1 && f2 >= f3) {
				return f2;
			}
			return f3;
		}
		
		/** Get the maximum of 4 float numbers */
		static inline float max(float f1, float f2, float f3, float f4)
		{
			float m = f1;
			if (f2 > m) {
				m = f2;
			}
			if (f3 > m) {
				m = f3;
			}
			if (f4 > m) {
				m = f4;
			}
			return m;
		}

		static inline float angle_sub_2pi(float x, float y)
		{
			float r = fmod(fabs(x - y), (float) (2 * M_PI));
			if (r > M_PI) {
				r = (float) (2.0 * M_PI - r);
			}

			return r;
		}

		static inline float angle_sub_pi(float x, float y)
		{
			float r = fmod(fabs(x - y), (float) M_PI);
			if (r > M_PI / 2.0) {
				r = (float)(M_PI - r);
			}
			return r;
		}

		static inline int goodf(float *f)
		{
			// the first is abnormal zero the second is +-inf or NaN 
			if ((((int *) f)[0] & 0x7f800000) == 0 || (((int *) f)[0] & 0x7f800000) == 255) {
				return 0;
			}
			return 1;
		}

		static string get_time_label();

		static const char* get_debug_image(const char* imagename);
		
		static void set_log_level(int argc, char *argv[]);

		static inline float eman_copysign(float a, float b)
		{
#ifndef WIN32
			return copysign(a, b);
#else
			int flip = -1;
			if ((a <= 0 && b <= 0) || (a > 0 && b > 0)) {
				flip = 1;
			}
			return a * flip;
#endif
		}

		static inline float eman_erfc(float x)
		{
#ifndef WIN32
			return (float)erfc(x);
#else
			static double a[] = { -1.26551223, 1.00002368,
								  0.37409196, 0.09678418,
								  -0.18628806, 0.27886807,
								  -1.13520398, 1.48851587,
								  -0.82215223, 0.17087277
			};

			double result = 1;
			double z = fabs(x);
			if (z > 0) {
				double t = 1 / (1 + 0.5 * z);
				double f1 =
					t * (a[4] + t * (a[5] + t * (a[6] + t * (a[7] + t * (a[8] + t * a[9])))));
				result = t * exp((-z * z) + a[0] + t * (a[1] + t * (a[2] + t * (a[3] + f1))));

				if (x < 0) {
					result = 2 - result;
				}
			}
			return (float)result;
#endif
		}

		
	};
}

#endif
