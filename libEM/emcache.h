#ifndef eman__emcache__h__
#define eman__emcache__h__ 1

#include <stdlib.h>
#include <string>
#include <assert.h>

using std::string;

namespace EMAN
{
    template <class T> class EMCache
    {
    public:
	EMCache(int cache_size)
	{
	    item_cache = new T *[cache_size];
	    name_cache = new string[cache_size];

	    size = cache_size;
	    nitems = 0;
	}

	~EMCache()
	{
	    for (int i = 0; i < nitems; i++) {
		delete item_cache[i];
		item_cache[i] = 0;
	    }
	    
	    delete [] item_cache;
	    item_cache = 0;

	    delete [] name_cache;
	    name_cache = 0;
	}


	T *get(string itemname) const
	{
	    T *result = 0;

	    for (int i = 0; i < nitems; i++) {
		if (name_cache[i] == itemname) {
		    assert(item_cache[i] != 0);
		    result = item_cache[i];
		    break;
		}
	    }

	    return result;
	}

	void add(string itemname, T * item)
	{
	    if (!item) {
		return;
	    }

	    if (nitems < size) {
		item_cache[nitems] = item;
		name_cache[nitems] = itemname;
		nitems++;
	    }
	    else {
		int r = (int) (1.0 * size * rand() / (RAND_MAX + 1.0));
		delete item_cache[r];
		item_cache[r] = 0;

		item_cache[r] = item;
		name_cache[r] = itemname;
	    }
	}

	int get_size() const
	{
	    return size;
	}

    private:
	T ** item_cache;
	string *name_cache;

	int size;
	int nitems;
    };

    class ImageIO;

    class GlobalCache
    {
    public:
	static GlobalCache *instance();

	ImageIO *get_imageio(string filename);
	void add_imageio(string filename, ImageIO * io);


    private:
	EMCache<ImageIO> *imageio_cache;
	static GlobalCache *global_cache;

	GlobalCache();
	GlobalCache(const GlobalCache & gc);
	~GlobalCache();
    };

}

#endif
