from pyspark import SparkContext
import Sliding, argparse

def solve_puzzle(master, output, height, width, slaves):
    global HEIGHT, WIDTH, level
    HEIGHT=height
    WIDTH=width
    level = 0

    sc = SparkContext(master, "python")

    sol = Sliding.solution(WIDTH, HEIGHT)
    
    frontierRDD = sc.parallelize([(Sliding.board_to_hash(WIDTH, HEIGHT, sol), 0)])
    boardsRDD = sc.parallelize([(Sliding.board_to_hash(WIDTH, HEIGHT, sol), 0)])
    #while frontierRDD.count() != 0:
    try:
        while frontierRDD.first():
            level += 1
            
            # get all frontier nodes as a flattened list of ONLY (key), NOT (key, value)
            frontierRDD = frontierRDD.flatMap(lambda v: Sliding.children(WIDTH, HEIGHT, Sliding.hash_to_board(WIDTH, HEIGHT, v[0])))
            
            # add new (chilq, level) pairs to all boards
            boardsRDD = boardsRDD + frontierRDD.map(lambda v: (Sliding.board_to_hash(WIDTH, HEIGHT, v), level))
            #boardsRDD = boardsRDD.partitionBy(8, partitionFunc)
            
            # only keep board seen at lowest level
            boardsRDD = boardsRDD.reduceByKey(lambda v1, v2: min(v1, v2))

            # frontier is only the boards that have the current level
            frontierRDD = boardsRDD.filter(lambda v: v[1] == level)

            # magic voodoo that it doesn't work without
            boardsRDD = boardsRDD.coalesce(slaves)
            frontierRDD = frontierRDD.coalesce(slaves)
    except:
        boardsRDD.coalesce(slaves).saveAsTextFile(output)
        sc.stop()



""" DO NOT EDIT PAST THIS LINE

You are welcome to read through the following code, but you
do not need to worry about understanding it.
"""

def main():
    """
    Parses command line arguments and runs the solver appropriately.
    If nothing is passed in, the default values are used.
    """
    parser = argparse.ArgumentParser(
            description="Returns back the entire solution graph.")
    parser.add_argument("-M", "--master", type=str, default="local[8]",
            help="url of the master for this job")
    parser.add_argument("-O", "--output", type=str, default="solution-out",
            help="name of the output file")
    parser.add_argument("-H", "--height", type=int, default=2,
            help="height of the puzzle")
    parser.add_argument("-W", "--width", type=int, default=2,
            help="width of the puzzle")
    parser.add_argument("-S", "--slaves", type=int, default=6,
            help="number of slaves executing the job")
    args = parser.parse_args()

    global PARTITION_COUNT
    PARTITION_COUNT = args.slaves * 16

    # call the puzzle solver
    solve_puzzle(args.master, args.output, args.height, args.width, args.slaves)

# begin execution if we are running this file directly
if __name__ == "__main__":
    main()
