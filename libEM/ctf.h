#ifndef eman__ctf__h__
#define eman__ctf__h__ 1

#include <string>
#include <map>
#include <math.h>
#include "emobject.h"

using std::string;
using std::map;

namespace EMAN
{
    class EMData;
    class XYData;

    class Ctf
    {
    public:	
	// NOTE: ctf is positive for the first peak, instead of negative
	enum CtfType {
	    CTF_NOISE,	        // the true ctf with B decay and with positive and negative peaks, 	
	    CTF_CTF_NO_BDECAY,	// the true ctf without B decay and with positive and negative peaks
	    CTF_AMP,	        // ctf ampltidue only = fabs(CTF_CTF)
	    CTF_AMP_NO_BDECAY,	// ctf ampltidue only = fabs(CTF_CTF_NO_B)
	    CTF_SIGN,	        // ctf sign (+-1)       = sign(CTF_CTF)
	    CTF_BFACTOR,	// B factor decay only, no ctf oscillation
	    CTF_BACKGROUND,	// Background, no ctf oscillation
	    CTF_SNR,	        // Signal to noise ratio
	    CTF_SNR_SIGN,	// Signal to noise ratio with sign = CTF_SNR*CTF_SIGN
	    CTF_WIENER_FILTER,	// Weiner Filter = 1/(1+1/snr)
	    CTF_WIENER_CTF_CORRECTION,	// ctf correction with Weiner Filter = 1/(ctf*exp(-b*s^2)*(1+1/snr))	
	    CTF_AMP_S,
	    CTF_NOISE_S,
	    CTF_ABS_AMP_S,
	    CTF_RELATIVE_SNR,
	    CTF_ABS_SNR,
	    CTF_SNR_WIENER,
	    CTF_WIENER_CTF_CORRECTION1,
	    CTF_WIENER_CTF_CORRECTION2,
	    CTF_TOTAL_CURVE
	};
    public:
	virtual ~Ctf() { }

	virtual int from_string(string ctf) = 0;
	virtual string to_string() const = 0;

	virtual void from_dict(const Dict & dict) = 0;
	virtual Dict to_dict() const = 0;
	
	virtual vector<float> compute_1d(EMData * img, CtfType t, XYData * struct_factor = 0) = 0;
	virtual void compute_2d_real(EMData * img, CtfType t, XYData * struct_factor = 0) = 0;
	virtual void compute_2d_complex(EMData * img, CtfType t, XYData * struct_factor = 0) = 0;

	virtual void copy_from(Ctf * new_ctf) = 0;
	
    public:
	enum { CTFOS = 5 };

    };


    class SimpleCtf: public Ctf
    {
    public:
	float defocus;		// 0
	float bfactor;		// 1
	float amplitude;	// 2
	float ampcont;		// 3
	float noise1;		// 4
	float noise2;		// 5
	float noise3;		// 6
	float noise4;		// 7
	float voltage;		// 8
	float cs;		// 9
	float apix;		// 10

    public:
	SimpleCtf();
	~SimpleCtf();

	vector<float> compute_1d(EMData * image, CtfType type, XYData * struct_factor = 0);
	void compute_2d_real(EMData * image, CtfType type, XYData * struct_factor = 0);
	void compute_2d_complex(EMData * image, CtfType type, XYData * struct_factor = 0);
	
	int from_string(string ctf);
	string to_string() const;

	void from_dict(const Dict & dict);
	Dict to_dict() const;
	
	void copy_from(Ctf * new_ctf);
	
    private:
	inline float calc_amp1()
	{
	    return (sqrt(1 - ampcont * ampcont));
	}
	
	inline float calc_lambda()
	{
	    float lambda = 12.2639 / sqrt(voltage * 1000.0 + 0.97845 * voltage * voltage);
	    return lambda;
	}
	
	inline float calc_g1()
	{
	    float lambda = calc_lambda();
	    float g1 = 2.5e6 * cs * lambda * lambda * lambda;
	    return g1;
	}

	inline float calc_g2()
	{
	    float lambda = calc_lambda();
	    float g2 = 5000.0 * defocus * lambda;
	    return g2;
	}
	
	inline float calc_gamma(float g1, float g2, float s)
	{
	    float s2 = s * s;
	    float gamma = -2 * M_PI * (g1 * s2 * s2 + g2 * s2);
	    return gamma;
	}

	inline float calc_ctf1(float g, float gamma, float s)
	{
	    float r = amplitude * exp(-(bfactor * s * s)) * (g * sin(gamma) + ampcont * cos(gamma));
	    return r;
	}

	inline float calc_amplitude(float gamma)
	{
	    float v = amplitude * (sqrt(1.0-ampcont*ampcont)*sin(gamma)+ampcont*cos(gamma));
	    return v;
	}
	
	inline float calc_noise(float s)
	{
	    float ns = M_PI / 2 * noise4 * s;
	    float ns2 = ns * ns;
	    float n = noise3 * exp(-ns2 - s * noise2 - sqrt(fabs(s)) * noise1);
	    return n;
	}

	inline float calc_ctf(float g1, float gamma, float s)
	{
	    float ctf1 = calc_ctf1(g1, gamma, s);
	    float ctf2 = ctf1 * ctf1 / calc_noise(s);
	    return ctf2;
	}

    };

}



#endif
