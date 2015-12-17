import os
import argparse
import matplotlib.pyplot as plt


_global_figlist = [ ]


def _publish_if_needed(fig, figname, publish):
    if publish is None: return
    pubname = os.path.join(publish[0], figname + '.' + publish[1])
    print "publishing", pubname
    plt.savefig(pubname)


def _get_name(figure_func):
    if hasattr(figure_func, 'name'):
        name = figure_func.name
    else:
        try:
            name = figure_func.__name__
        except AttributeError:
            name = figure_func.__class__.__name__
    return name


def set_figlist(figlist):
    del _global_figlist[:]
    for f in figlist: _global_figlist.append(f)


def get_figlist():
    return list(_global_figlist)


def exec_figure(figure_func, interactive=False, publish=None):
    """Execute a callable 'figure_func' that receives a pyplot.Figure instance as
    its only required argument. Use interactive=True if running repeatedly from
    ipython or emacs, so that the figure instance will be re-used if it is still
    open (it will be created again if it was closed). Set publish=['fig-dir',
    'pdf'] for example to save the figure as a pdf document in the directory
    'fig-dir'. If figure_func has attributes 'size' or 'name', those will be
    used in place of defaults to set the figure size, window title, and
    published file name. Return the figure instance.

    """

    figsize = getattr(figure_func, 'size', [8, 8])
    figname = _get_name(figure_func)
    fignum = 1

    if interactive: plt.ion()
    else: plt.ioff()
    fig = plt.figure(fignum, figsize=figsize)
    fig.canvas.set_window_title(figname)

    if interactive:
        if plt.fignum_exists(fignum): fig.clear()
        else: plt.show()
        figure_func(fig)
        plt.draw()
        _publish_if_needed(fig, figname, publish)
    else:
        figure_func(fig)
        _publish_if_needed(fig, figname, publish)
        plt.show()

    return fig


def publish_all(figlist=None, directory='.', reuse=False, publish=['.', 'pdf']):
    """Publish a whole list of figures. Use the global list if figlist is None.

    """
    if figlist is None: figlist = _global_figlist
    for f in figlist:
        figname = _get_name(f)
        fig = exec_figure(f, interactive=True, publish=publish)
        if not reuse:
            plt.close(fig)


def run_main(figlist=None, directory='.'):
    """Dispatch a list of figures from the command line. Use the global list if
    figlist is None.

    """
    if figlist is None: figlist = _global_figlist
    figdict = dict([(_get_name(f), f) for f in figlist])

    parser = argparse.ArgumentParser()
    parser.add_argument('fignames', nargs='+', choices=['all'] + figdict.keys())
    parser.add_argument('--publish', default='')
    parser.add_argument('--directory', '-d', default=directory)
    parser.add_argument('--reuse-fig', action='store_true',
                        help='reuse the same window for all figures')
    args = parser.parse_args()

    if args.publish:
        publish = [args.directory, args.publish]
    else:
        publish = None

    if args.fignames[0] == 'all':
        args.fignames = [_get_name(f) for f in figlist]

    for figname in args.fignames:
        fig = exec_figure(figdict[figname], interactive=publish, publish=publish)
        if publish and not args.reuse_fig:
            plt.close(fig)
